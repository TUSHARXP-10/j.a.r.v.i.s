from pydantic import BaseModel, EmailStr
from typing import List, Dict, Any, Optional
from datetime import datetime

class NodeConfig(BaseModel):
    label: str
    config: Dict[str, Any] = {}

class Node(BaseModel):
    id: str
    type: str
    position: Dict[str, float]
    data: NodeConfig

class Edge(BaseModel):
    id: str
    source: str
    target: str
    sourceHandle: Optional[str] = None
    targetHandle: Optional[str] = None

class WorkflowCreate(BaseModel):
    name: str
    description: Optional[str] = None
    nodes: List[Node]
    edges: List[Edge]

class WorkflowResponse(BaseModel):
    id: int
    name: str
    description: Optional[str]
    nodes: List[Node]
    edges: List[Edge]
    created_at: datetime
    updated_at: Optional[datetime]

    class Config:
        from_attributes = True

# Authentication Schemas
class UserCreate(BaseModel):
    username: str
    email: EmailStr
    password: str
    full_name: Optional[str] = None

class UserLogin(BaseModel):
    username: str
    password: str

class UserResponse(BaseModel):
    id: int
    username: str
    email: EmailStr
    full_name: Optional[str]
    role: str
    is_active: bool
    created_at: datetime
    updated_at: Optional[datetime]

    class Config:
        from_attributes = True

class Token(BaseModel):
    access_token: str
    token_type: str
    expires_in: int
    user: UserResponse

class TokenData(BaseModel):
    username: Optional[str] = None
    user_id: Optional[int] = None
    role: Optional[str] = None

class WorkflowExecutionLogResponse(BaseModel):
    id: int
    workflow_id: int
    schedule_id: Optional[int]
    execution_time: datetime
    status: str
    input_data: Optional[Dict[str, Any]]
    output_data: Optional[Dict[str, Any]]
    error_message: Optional[str]
    created_at: datetime

    class Config:
        from_attributes = True

class WorkflowExecutionLogFilter(BaseModel):
    status: Optional[str] = None
    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None
    schedule_id: Optional[int] = None

class WorkflowScheduleCreate(BaseModel):
    name: str
    cron_expression: str
    is_active: int = 1
    input_data: Optional[Dict[str, Any]] = {}

class WorkflowScheduleResponse(BaseModel):
    id: int
    workflow_id: int
    name: str
    cron_expression: str
    is_active: int
    input_data: Optional[Dict[str, Any]]
    created_at: datetime
    updated_at: Optional[datetime]

    class Config:
        from_attributes = True

class WorkflowExecutionRequest(BaseModel):
    input_data: Dict[str, Any] = {}

class WorkflowRunResponse(BaseModel):
    id: int
    workflow_id: int
    status: str
    result: Optional[Dict[str, Any]]
    logs: Optional[List[Dict[str, Any]]]
    created_at: datetime
    updated_at: Optional[datetime]

    class Config:
        from_attributes = True

# Workflow Sharing Schemas
class WorkflowShareCreate(BaseModel):
    user_id: int
    permission_level: str  # 'view' or 'edit'

class WorkflowShareUpdate(BaseModel):
    permission_level: str  # 'view' or 'edit'

class WorkflowShareResponse(BaseModel):
    id: int
    workflow_id: int
    user_id: int
    permission_level: str
    created_at: datetime
    updated_at: Optional[datetime]
    user: UserResponse

    class Config:
        from_attributes = True

class WorkflowCollaboratorResponse(BaseModel):
    id: int
    username: str
    email: str
    full_name: Optional[str]
    role: str
    permission_level: str
    shared_at: datetime

    class Config:
        from_attributes = True