"""
Redis Streams client with consumer group support.
Implements idempotent message processing with ACKs and retries.
"""
import json
import logging
import asyncio
from typing import Dict, Any, Optional, List, Tuple
from datetime import datetime, timedelta
import redis.asyncio as redis
from redis.exceptions import ResponseError, ConnectionError
from tenacity import retry, stop_after_attempt, wait_exponential

from orchestrator.app.core.config import settings

logger = logging.getLogger(__name__)


class RedisStreamsClient:
    """
    Redis Streams client with consumer group support.
    Handles connection pooling, retries, and ACKs.
    """
    
    def __init__(self):
        """Initialize Redis client with connection pool."""
        self.pool = redis.ConnectionPool.from_url(
            settings.redis_url,
            max_connections=50,
            decode_responses=True
        )
        self.client: Optional[redis.Redis] = None
        self.consumer_name = f"orchestrator_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        
    async def connect(self) -> None:
        """Establish Redis connection."""
        try:
            self.client = redis.Redis(connection_pool=self.pool)
            await self.client.ping()
            logger.info(f"✅ Redis connected: {settings.redis_host}:{settings.redis_port}")
        except ConnectionError as e:
            logger.error(f"❌ Redis connection failed: {e}")
            raise
    
    async def disconnect(self) -> None:
        """Close Redis connection."""
        if self.client:
            await self.client.aclose()
            await self.pool.aclose()
            logger.info("Redis connection closed")
    
    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=2, max=10)
    )
    async def create_consumer_group(
        self,
        stream_key: str,
        group_name: str,
        start_id: str = "0"
    ) -> bool:
        """
        Create consumer group if not exists.
        
        Args:
            stream_key: Redis stream key
            group_name: Consumer group name
            start_id: Starting message ID (0 = from beginning, $ = new messages only)
            
        Returns:
            bool: True if group created or already exists
        """
        try:
            await self.client.xgroup_create(
                stream_key,
                group_name,
                id=start_id,
                mkstream=True
            )
            logger.info(f"✅ Consumer group created: {group_name} on {stream_key}")
            return True
        except ResponseError as e:
            if "BUSYGROUP" in str(e):
                logger.debug(f"Consumer group already exists: {group_name}")
                return True
            logger.error(f"Failed to create consumer group: {e}")
            raise
    
    async def add_to_stream(
        self,
        stream_key: str,
        data: Dict[str, Any],
        max_len: Optional[int] = None
    ) -> str:
        """
        Add message to Redis stream.
        
        Args:
            stream_key: Redis stream key
            data: Message data as dict
            max_len: Maximum stream length (for trimming)
            
        Returns:
            str: Message ID
        """
        try:
            # Convert dict to flat key-value pairs for XADD
            flat_data = {"payload": json.dumps(data)}
            
            message_id = await self.client.xadd(
                stream_key,
                flat_data,
                maxlen=max_len or settings.stream_max_len,
                approximate=True
            )
            logger.debug(f"Message added to {stream_key}: {message_id}")
            return message_id
        except Exception as e:
            logger.error(f"Failed to add message to stream: {e}")
            raise
    
    async def consume_messages(
        self,
        stream_key: str,
        group_name: str,
        count: int = 1,
        block: int = 5000
    ) -> List[Tuple[str, Dict[str, Any]]]:
        """
        Consume messages from stream using consumer group.
        
        Args:
            stream_key: Redis stream key
            group_name: Consumer group name
            count: Number of messages to consume
            block: Block time in milliseconds (0 = non-blocking)
            
        Returns:
            List of (message_id, data) tuples
        """
        try:
            # Read from group
            messages = await self.client.xreadgroup(
                group_name,
                self.consumer_name,
                {stream_key: ">"},
                count=count,
                block=block
            )
            
            if not messages:
                return []
            
            # Parse messages
            result = []
            for stream, stream_messages in messages:
                for msg_id, msg_data in stream_messages:
                    try:
                        payload = json.loads(msg_data.get("payload", "{}"))
                        result.append((msg_id, payload))
                    except json.JSONDecodeError as e:
                        logger.error(f"Failed to parse message {msg_id}: {e}")
                        # ACK malformed message to prevent blocking
                        await self.ack_message(stream_key, group_name, msg_id)
            
            return result
        except Exception as e:
            logger.error(f"Failed to consume messages: {e}")
            return []
    
    async def ack_message(
        self,
        stream_key: str,
        group_name: str,
        message_id: str
    ) -> bool:
        """
        Acknowledge message processing.
        
        Args:
            stream_key: Redis stream key
            group_name: Consumer group name
            message_id: Message ID to acknowledge
            
        Returns:
            bool: True if acknowledged
        """
        try:
            result = await self.client.xack(stream_key, group_name, message_id)
            logger.debug(f"Message ACKed: {message_id}")
            return result > 0
        except Exception as e:
            logger.error(f"Failed to ACK message {message_id}: {e}")
            return False
    
    async def claim_pending_messages(
        self,
        stream_key: str,
        group_name: str,
        min_idle_time: int = 60000,
        count: int = 10
    ) -> List[Tuple[str, Dict[str, Any]]]:
        """
        Claim pending messages that have been idle too long.
        Useful for recovering from consumer failures.
        
        Args:
            stream_key: Redis stream key
            group_name: Consumer group name
            min_idle_time: Minimum idle time in milliseconds
            count: Number of messages to claim
            
        Returns:
            List of (message_id, data) tuples
        """
        try:
            # Get pending messages info
            pending_info = await self.client.xpending_range(
                stream_key,
                group_name,
                min="-",
                max="+",
                count=count
            )
            
            if not pending_info:
                return []
            
            # Claim messages that are idle
            claimed = []
            for info in pending_info:
                msg_id = info["message_id"]
                idle_time = info["time_since_delivered"]
                
                if idle_time >= min_idle_time:
                    result = await self.client.xclaim(
                        stream_key,
                        group_name,
                        self.consumer_name,
                        min_idle_time,
                        [msg_id]
                    )
                    
                    for msg_id, msg_data in result:
                        try:
                            payload = json.loads(msg_data.get("payload", "{}"))
                            claimed.append((msg_id, payload))
                        except json.JSONDecodeError:
                            await self.ack_message(stream_key, group_name, msg_id)
            
            if claimed:
                logger.info(f"Claimed {len(claimed)} pending messages")
            
            return claimed
        except Exception as e:
            logger.error(f"Failed to claim pending messages: {e}")
            return []
    
    async def set_cache(
        self,
        key: str,
        value: Any,
        ttl: Optional[int] = None
    ) -> bool:
        """
        Set cache value with optional TTL.
        
        Args:
            key: Cache key
            value: Value to cache (will be JSON serialized)
            ttl: Time to live in seconds
            
        Returns:
            bool: True if set successfully
        """
        try:
            serialized = json.dumps(value)
            if ttl:
                await self.client.setex(key, ttl, serialized)
            else:
                await self.client.set(key, serialized)
            return True
        except Exception as e:
            logger.error(f"Failed to set cache {key}: {e}")
            return False
    
    async def get_cache(self, key: str) -> Optional[Any]:
        """
        Get cached value.
        
        Args:
            key: Cache key
            
        Returns:
            Cached value or None
        """
        try:
            value = await self.client.get(key)
            if value:
                return json.loads(value)
            return None
        except Exception as e:
            logger.error(f"Failed to get cache {key}: {e}")
            return None
    
    async def acquire_lock(
        self,
        lock_key: str,
        timeout: int = 30
    ) -> bool:
        """
        Acquire distributed lock.
        
        Args:
            lock_key: Lock identifier
            timeout: Lock timeout in seconds
            
        Returns:
            bool: True if lock acquired
        """
        try:
            return await self.client.set(
                lock_key,
                self.consumer_name,
                nx=True,
                ex=timeout
            )
        except Exception as e:
            logger.error(f"Failed to acquire lock {lock_key}: {e}")
            return False
    
    async def release_lock(self, lock_key: str) -> bool:
        """
        Release distributed lock.
        
        Args:
            lock_key: Lock identifier
            
        Returns:
            bool: True if released
        """
        try:
            result = await self.client.delete(lock_key)
            return result > 0
        except Exception as e:
            logger.error(f"Failed to release lock {lock_key}: {e}")
            return False
    
    async def health_check(self) -> bool:
        """
        Check Redis connection health.
        
        Returns:
            bool: True if healthy
        """
        try:
            await self.client.ping()
            return True
        except Exception:
            return False


# Global Redis client instance
redis_client = RedisStreamsClient()