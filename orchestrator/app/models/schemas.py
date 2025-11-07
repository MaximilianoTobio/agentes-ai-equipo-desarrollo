"""
Pydantic models for request/response validation.
Implements strict typing for all API interactions.
"""
from datetime import datetime
from typing import Optional, Dict, Any, List, Literal
from pydantic import BaseModel, Field, ConfigDict
from uuid import UUID
from enum import Enum


class TaskStatus(str, Enum):
    """Task lifecycle states."""
    PENDING = "pending"
    ASSIGNED = "assigned"
    IN_PROGRESS = "in_progress"
    IN_REVIEW = "in_review"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class TaskType(str, Enum):
    """Types of tasks the system can handle."""
    FEATURE = "feature"
    BUG_FIX = "bug_fix"
    REFACTOR = "refactor"
    TEST = "test"
    DOCUMENTATION = "documentation"


class AgentType(str, Enum):
    """Available agent types in the system."""
    DEV_AGENT = "dev_agent"
    QA_AGENT = "qa_agent"
    REVIEW_AGENT = "review_agent"
    REFACTOR_AGENT = "refactor_agent"
    PAIR_COORDINATOR = "pair_coordinator"


# === Task Schemas ===

class TaskCreate(BaseModel):
    """Schema for creating a new task."""
    title: str = Field(..., min_length=3, max_length=200)
    description: str = Field(..., min_length=10, max_length=5000)
    task_type: TaskType
    assigned_agent: Optional[AgentType] = None
    priority: int = Field(default=1, ge=1, le=5)
    metadata: Optional[Dict[str, Any]] = None
    
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "title": "Implement user authentication",
                "description": "Create a secure authentication system with JWT tokens",
                "task_type": "feature",
                "assigned_agent": "dev_agent",
                "priority": 2,
                "metadata": {"sprint": "1", "story_points": 5}
            }
        }
    )


class TaskUpdate(BaseModel):
    """Schema for updating an existing task."""
    title: Optional[str] = Field(None, min_length=3, max_length=200)
    description: Optional[str] = Field(None, min_length=10, max_length=5000)
    status: Optional[TaskStatus] = None
    assigned_agent: Optional[AgentType] = None
    priority: Optional[int] = Field(None, ge=1, le=5)
    result: Optional[Dict[str, Any]] = None
    metadata: Optional[Dict[str, Any]] = None


class TaskResponse(BaseModel):
    """Schema for task responses."""
    id: UUID
    title: str
    description: str
    task_type: TaskType
    status: TaskStatus
    assigned_agent: Optional[AgentType] = None
    priority: int
    created_at: datetime
    updated_at: datetime
    completed_at: Optional[datetime] = None
    result: Optional[Dict[str, Any]] = None
    metadata: Optional[Dict[str, Any]] = None
    retry_count: int = 0
    
    model_config = ConfigDict(from_attributes=True)


class TaskListResponse(BaseModel):
    """Schema for paginated task list."""
    tasks: List[TaskResponse]
    total: int
    page: int
    page_size: int
    has_next: bool
    has_prev: bool


# === Health Check Schemas ===

class ServiceHealth(BaseModel):
    """Health status of a service."""
    name: str
    status: Literal["healthy", "degraded", "unhealthy"]
    latency_ms: Optional[float] = None
    details: Optional[Dict[str, Any]] = None


class HealthCheckResponse(BaseModel):
    """Complete health check response."""
    status: Literal["healthy", "degraded", "unhealthy"]
    version: str
    timestamp: datetime
    services: List[ServiceHealth]
    metrics: Dict[str, Any] = Field(default_factory=dict)


# === Metrics Schemas ===

class MetricsResponse(BaseModel):
    """Prometheus-style metrics response."""
    timestamp: datetime
    orchestrator: Dict[str, Any]
    agents: Dict[str, Any]
    tasks: Dict[str, Any]
    llm: Dict[str, Any]


# === Pair Programming Schemas ===

class PairSessionCreate(BaseModel):
    """Schema for creating pair programming session."""
    task_id: UUID
    driver_agent: AgentType
    navigator_agent: AgentType
    max_iterations: int = Field(default=5, ge=1, le=10)


class PairSessionResponse(BaseModel):
    """Schema for pair session responses."""
    id: UUID
    task_id: UUID
    driver_agent: AgentType
    navigator_agent: AgentType
    status: Literal["active", "completed", "failed"]
    iteration_count: int
    max_iterations: int
    created_at: datetime
    completed_at: Optional[datetime] = None
    total_tokens_used: int = 0
    
    model_config = ConfigDict(from_attributes=True)


# === Event Schemas (for Outbox Pattern) ===

class OutboxEventCreate(BaseModel):
    """Schema for creating outbox events."""
    aggregate_id: UUID
    event_type: str = Field(..., min_length=3, max_length=100)
    payload: Dict[str, Any]


class OutboxEventResponse(BaseModel):
    """Schema for outbox event responses."""
    id: UUID
    aggregate_id: UUID
    event_type: str
    payload: Dict[str, Any]
    created_at: datetime
    processed_at: Optional[datetime] = None
    retry_count: int = 0
    
    model_config = ConfigDict(from_attributes=True)


# === Error Schemas ===

class ErrorResponse(BaseModel):
    """Standard error response."""
    error: str
    detail: Optional[str] = None
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    request_id: Optional[str] = None


# === Token Budget Schemas ===

class TokenBudgetStatus(BaseModel):
    """Current token budget status."""
    daily_budget: int
    daily_used: int
    daily_remaining: int
    daily_percentage: float
    sprint_budget: int
    sprint_used: int
    sprint_remaining: int
    sprint_percentage: float
    last_reset: datetime
    alert_triggered: bool