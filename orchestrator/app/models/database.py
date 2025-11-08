"""
Database models and connection management.
Implements SQLAlchemy async models with connection pooling and lazy engine initialization.
"""
import logging
from contextlib import asynccontextmanager
from typing import AsyncGenerator, Optional
from datetime import datetime

from sqlalchemy.ext.asyncio import (
    AsyncSession,
    create_async_engine,
    async_sessionmaker,
    AsyncEngine
)
from sqlalchemy.orm import declarative_base, Mapped, mapped_column
from sqlalchemy import (
    String, Integer, DateTime, Text, JSON, Boolean, func, Index, text
)
from sqlalchemy.dialects.postgresql import UUID
import uuid

from orchestrator.app.core.config import settings

logger = logging.getLogger(__name__)

# Declarative base for models
Base = declarative_base()

# Global variables for lazy initialization
_engine: Optional[AsyncEngine] = None
_session_factory: Optional[async_sessionmaker] = None


def get_engine() -> AsyncEngine:
    """
    Get or create async engine with lazy initialization.
    This ensures engine uses current settings, not cached values.
    """
    global _engine
    if _engine is None:
        logger.info(f"Creating database engine with URL: {settings.database_url.split('@')[1]}")
        _engine = create_async_engine(
            settings.database_url,
            echo=settings.debug,
            pool_size=20,
            max_overflow=40,
            pool_pre_ping=True,
            pool_recycle=3600,
        )
    return _engine


def get_session_factory() -> async_sessionmaker:
    """Get or create async session factory."""
    global _session_factory
    if _session_factory is None:
        _session_factory = async_sessionmaker(
            get_engine(),
            class_=AsyncSession,
            expire_on_commit=False,
            autocommit=False,
            autoflush=False,
        )
    return _session_factory


# === Database Models ===

class TaskModel(Base):
    """Task database model."""
    __tablename__ = "tasks"
    __table_args__ = (
        Index('idx_tasks_status', 'status'),
        Index('idx_tasks_created_at', 'created_at'),
        Index('idx_tasks_assigned_agent', 'assigned_agent'),
        {'schema': 'agent_system'}
    )
    
    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4
    )
    title: Mapped[str] = mapped_column(String(200), nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=False)
    task_type: Mapped[str] = mapped_column(String(50), nullable=False)
    status: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
        default="pending"
    )
    assigned_agent: Mapped[str | None] = mapped_column(String(50), nullable=True)
    priority: Mapped[int] = mapped_column(Integer, nullable=False, default=1)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
        onupdate=func.now()
    )
    completed_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True
    )
    result: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    task_metadata: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    retry_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)


class OutboxEventModel(Base):
    """Outbox event model for transactional outbox pattern."""
    __tablename__ = "outbox_events"
    __table_args__ = (
        Index('idx_outbox_processed', 'processed_at'),
        Index('idx_outbox_created', 'created_at'),
        {'schema': 'agent_system'}
    )
    
    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4
    )
    aggregate_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        nullable=False
    )
    event_type: Mapped[str] = mapped_column(String(100), nullable=False)
    payload: Mapped[dict] = mapped_column(JSON, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now()
    )
    processed_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True
    )
    retry_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)


class AuditTrailModel(Base):
    """Audit trail for all system actions."""
    __tablename__ = "audit_trail"
    __table_args__ = (
        Index('idx_audit_entity_id', 'entity_id'),
        Index('idx_audit_timestamp', 'timestamp'),
        {'schema': 'agent_system'}
    )
    
    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4
    )
    entity_type: Mapped[str] = mapped_column(String(50), nullable=False)
    entity_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        nullable=False
    )
    action: Mapped[str] = mapped_column(String(50), nullable=False)
    actor: Mapped[str] = mapped_column(String(100), nullable=False)
    changes: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    timestamp: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now()
    )
    audit_metadata: Mapped[dict | None] = mapped_column(JSON, nullable=True)


class PairSessionModel(Base):
    """Pair programming session model."""
    __tablename__ = "pair_sessions"
    __table_args__ = (
        Index('idx_pair_task_id', 'task_id'),
        Index('idx_pair_status', 'status'),
        {'schema': 'agent_system'}
    )
    
    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4
    )
    task_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        nullable=False
    )
    driver_agent: Mapped[str] = mapped_column(String(50), nullable=False)
    navigator_agent: Mapped[str] = mapped_column(String(50), nullable=False)
    status: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
        default="active"
    )
    iteration_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    max_iterations: Mapped[int] = mapped_column(Integer, nullable=False, default=5)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now()
    )
    completed_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True
    )
    final_code: Mapped[str | None] = mapped_column(Text, nullable=True)
    total_tokens_used: Mapped[int] = mapped_column(Integer, nullable=False, default=0)


# === Connection Management ===

@asynccontextmanager
async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """
    Dependency to get database session.
    Ensures proper cleanup and transaction management.
    
    Usage:
        async with get_db() as db:
            result = await db.execute(query)
    """
    session_factory = get_session_factory()
    async with session_factory() as session:
        try:
            yield session
            await session.commit()
        except Exception as e:
            await session.rollback()
            logger.error(f"Database error: {e}")
            raise
        finally:
            await session.close()


async def init_db() -> None:
    """
    Initialize database tables.
    
    NOTE: In production, use Alembic migrations instead.
    This is only for development/testing.
    """
    try:
        engine = get_engine()
        async with engine.begin() as conn:
            # Create schema if not exists
            await conn.execute(
                text(f"CREATE SCHEMA IF NOT EXISTS {settings.postgres_schema}")
            )
            # Create all tables
            await conn.run_sync(Base.metadata.create_all)
        
        logger.info("✅ Database initialized successfully")
    except Exception as e:
        logger.error(f"❌ Database initialization failed: {e}")
        raise


async def close_db() -> None:
    """Close database connections and dispose engine."""
    global _engine, _session_factory
    if _engine is not None:
        await _engine.dispose()
        _engine = None
        _session_factory = None
        logger.info("Database connections closed")


async def health_check_db() -> bool:
    """
    Check database health.
    
    Returns:
        bool: True if database is healthy
    """
    try:
        async with get_db() as session:
            await session.execute(text("SELECT 1"))
        return True
    except Exception as e:
        logger.error(f"Database health check failed: {e}")
        return False
