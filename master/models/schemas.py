from pydantic import BaseModel, Field
from typing import Dict, List, Optional, Any
from enum import Enum
from datetime import datetime

class TaskStatus(str, Enum):
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"

class FindingSeverity(str, Enum):
    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"
    INFO = "info"

class WorkerStatus(str, Enum):
    ACTIVE = "active"
    IDLE = "idle"
    OFFLINE = "offline"
    ERROR = "error"

class TaskCreate(BaseModel):
    target: str
    wordlist_name: str
    wordlist_path: str
    options: Dict[str, Any] = Field(default_factory=dict)
    worker_ids: List[str] = Field(default_factory=list)

class TaskResponse(BaseModel):
    task_id: str
    target: str
    status: TaskStatus
    progress: float
    created_at: datetime
    completed_at: Optional[datetime]
    worker_ids: List[str]
    findings_count: int = 0

class WorkerInfo(BaseModel):
    worker_id: str
    status: WorkerStatus
    hostname: str
    threads: int
    current_task: Optional[str]
    last_seen: datetime
    tasks_completed: int = 0

class Finding(BaseModel):
    finding_id: str
    task_id: str
    url: str
    status_code: int
    content_length: int
    words: int
    lines: int
    severity: FindingSeverity
    detected_issues: List[str]
    raw_response: Optional[str]
    checked: bool = False
    created_at: datetime

class ScanConfig(BaseModel):
    name: str
    target: str
    wordlist: str
    threads_per_worker: int = Field(ge=1, le=100)
    rate_limit: Optional[int]
    follow_redirects: bool = True
    recursive: bool = False
    extensions: List[str] = Field(default_factory=list)
    headers: Dict[str, str] = Field(default_factory=dict)
