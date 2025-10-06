from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey, JSON, Boolean
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from database import Base
from passlib.context import CryptContext

# Password hashing context
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String(50), unique=True, index=True, nullable=False)
    email = Column(String(100), unique=True, index=True, nullable=False)
    hashed_password = Column(String(255), nullable=False)
    full_name = Column(String(100), nullable=True)
    role = Column(String(20), default="viewer", nullable=False)  # admin, creator, viewer
    is_active = Column(Boolean, default=True, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    # Relationships
    workflows = relationship("Workflow", back_populates="owner")
    schedules = relationship("WorkflowSchedule", back_populates="owner")

    def verify_password(self, password: str) -> bool:
        """Verify a password against the hashed password."""
        return pwd_context.verify(password, self.hashed_password)

    def set_password(self, password: str):
        """Hash and set the password."""
        self.hashed_password = pwd_context.hash(password)

    def has_role(self, required_role: str) -> bool:
        """Check if user has a specific role or higher."""
        role_hierarchy = {"viewer": 1, "creator": 2, "admin": 3}
        user_level = role_hierarchy.get(self.role, 0)
        required_level = role_hierarchy.get(required_role, 0)
        return user_level >= required_level

    def can_edit_workflow(self, workflow) -> bool:
        """Check if user can edit a specific workflow."""
        if self.has_role("admin"):
            return True
        if workflow.owner_id == self.id and self.has_role("creator"):
            return True
        # Check if user has edit permission through sharing
        return any(share.user_id == self.id and share.permission_level == "edit" for share in workflow.shares)

    def can_view_workflow(self, workflow) -> bool:
        """Check if user can view a specific workflow."""
        if self.has_role("admin"):
            return True
        if workflow.owner_id == self.id:
            return True
        if workflow.is_public:
            return True
        # Check if user has been shared this workflow
        return any(share.user_id == self.id for share in workflow.shares)

    def get_workflow_permission(self, workflow) -> str:
        """Get user's permission level for a specific workflow."""
        if self.has_role("admin") or workflow.owner_id == self.id:
            return "edit"
        if workflow.is_public:
            return "view"
        # Check shared permissions
        for share in workflow.shares:
            if share.user_id == self.id:
                return share.permission_level
        return None

    def can_share_workflow(self, workflow) -> bool:
        """Check if user can share a specific workflow."""
        return workflow.owner_id == self.id or self.has_role("admin")

class Workflow(Base):
    __tablename__ = "workflows"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    nodes = Column(JSON, nullable=False)
    edges = Column(JSON, nullable=False)
    owner_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    is_public = Column(Boolean, default=False, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    # Relationships
    owner = relationship("User", back_populates="workflows")
    runs = relationship("WorkflowRun", back_populates="workflow", cascade="all, delete-orphan")
    schedules = relationship("WorkflowSchedule", back_populates="workflow", cascade="all, delete-orphan")
    shares = relationship("WorkflowShare", back_populates="workflow", cascade="all, delete-orphan")

class WorkflowRun(Base):
    __tablename__ = "workflow_runs"

    id = Column(Integer, primary_key=True, index=True)
    workflow_id = Column(Integer, ForeignKey("workflows.id"), nullable=False)
    status = Column(String(50), nullable=False)  # 'pending', 'running', 'completed', 'failed'
    result = Column(JSON, nullable=True)
    logs = Column(JSON, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    # Relationship to workflow
    workflow = relationship("Workflow", back_populates="runs")

class WorkflowSchedule(Base):
    __tablename__ = "workflow_schedules"

    id = Column(Integer, primary_key=True, index=True)
    workflow_id = Column(Integer, ForeignKey("workflows.id"), nullable=False)
    owner_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    name = Column(String(255), nullable=False)
    cron_expression = Column(String(255), nullable=False)  # Cron expression for scheduling
    is_active = Column(Integer, default=1)  # 1 for active, 0 for inactive
    input_data = Column(JSON, nullable=True)  # Optional input data for scheduled runs
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    # Relationships
    workflow = relationship("Workflow", back_populates="schedules")
    owner = relationship("User", back_populates="schedules")

class WorkflowExecutionLog(Base):
    __tablename__ = "workflow_execution_logs"

    id = Column(Integer, primary_key=True, index=True)
    workflow_id = Column(Integer, ForeignKey('workflows.id'), nullable=False)
    user_id = Column(Integer, ForeignKey('users.id'), nullable=True)  # User who triggered the execution
    schedule_id = Column(Integer, ForeignKey('workflow_schedules.id'), nullable=True)  # Nullable for manual runs
    execution_time = Column(DateTime(timezone=True), server_default=func.now())
    status = Column(String(50), nullable=False)  # 'success', 'error'
    input_data = Column(JSON, nullable=True)
    output_data = Column(JSON, nullable=True)
    error_message = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    # Relationships
    workflow = relationship("Workflow")
    user = relationship("User")
    schedule = relationship("WorkflowSchedule")

class WorkflowShare(Base):
    __tablename__ = "workflow_shares"

    id = Column(Integer, primary_key=True, index=True)
    workflow_id = Column(Integer, ForeignKey('workflows.id'), nullable=False)
    user_id = Column(Integer, ForeignKey('users.id'), nullable=False)
    permission_level = Column(String(20), nullable=False)  # 'view' or 'edit'
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    # Relationships
    workflow = relationship("Workflow", back_populates="shares")
    user = relationship("User")

    # Unique constraint to prevent duplicate shares
    __table_args__ = (
        {'sqlite_autoincrement': True},
    )