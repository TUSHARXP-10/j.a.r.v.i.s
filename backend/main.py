from fastapi import FastAPI, HTTPException, Depends, UploadFile, File
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session
from typing import List, Optional, Dict, Any
import uvicorn
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger
from croniter import croniter
import json
from datetime import datetime, timedelta
import io
import zipfile

from database import get_db, init_db
from models import Workflow, WorkflowRun, WorkflowSchedule, WorkflowExecutionLog, User, WorkflowShare
from schemas import WorkflowCreate, WorkflowResponse, WorkflowRunResponse, WorkflowExecutionRequest, WorkflowScheduleCreate, WorkflowScheduleResponse, WorkflowExecutionLogResponse, WorkflowExecutionLogFilter, UserCreate, UserLogin, UserResponse, Token, WorkflowShareCreate, WorkflowShareUpdate, WorkflowShareResponse, WorkflowCollaboratorResponse
from workflow_runner import WorkflowRunner
from auth import (
    verify_password, get_password_hash, create_access_token, 
    get_current_active_user, require_admin, require_creator_or_admin,
    check_workflow_permission, ACCESS_TOKEN_EXPIRE_MINUTES
)
from plugin_manager import plugin_manager

app = FastAPI(
    title="Workflow Engine API",
    description="Backend API for workflow management and execution",
    version="1.0.0"
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://localhost:5174", "http://localhost:5175"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize workflow runner
workflow_runner = WorkflowRunner()

# Initialize scheduler
scheduler = BackgroundScheduler()
scheduled_jobs = {}  # Store job references

@app.on_event("startup")
def startup_event():
    init_db()
    scheduler.start()
    load_existing_schedules()
    # Load built-in plugins
    plugin_manager.load_builtin_plugins()

@app.on_event("shutdown")
def shutdown_event():
    scheduler.shutdown()

@app.get("/")
def read_root():
    return {"message": "Workflow Engine API", "version": "1.0.0"}

# Authentication endpoints
@app.post("/auth/register", response_model=Token)
def register_user(user: UserCreate, db: Session = Depends(get_db)):
    """Register a new user"""
    # Check if username already exists
    db_user = db.query(User).filter(User.username == user.username).first()
    if db_user:
        raise HTTPException(status_code=400, detail="Username already registered")
    
    # Check if email already exists
    db_user = db.query(User).filter(User.email == user.email).first()
    if db_user:
        raise HTTPException(status_code=400, detail="Email already registered")
    
    # Create new user
    hashed_password = get_password_hash(user.password)
    db_user = User(
        username=user.username,
        email=user.email,
        hashed_password=hashed_password,
        full_name=user.full_name
    )
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    
    # Create access token
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": db_user.username, "user_id": db_user.id, "role": db_user.role},
        expires_delta=access_token_expires
    )
    
    return {
        "access_token": access_token,
        "token_type": "bearer",
        "expires_in": ACCESS_TOKEN_EXPIRE_MINUTES * 60,
        "user": db_user
    }

@app.post("/auth/login", response_model=Token)
def login_user(user: UserLogin, db: Session = Depends(get_db)):
    """Login user and return JWT token"""
    # Find user by username
    db_user = db.query(User).filter(User.username == user.username).first()
    if not db_user or not db_user.verify_password(user.password):
        raise HTTPException(status_code=401, detail="Incorrect username or password")
    
    if not db_user.is_active:
        raise HTTPException(status_code=400, detail="Inactive user")
    
    # Create access token
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": db_user.username, "user_id": db_user.id, "role": db_user.role},
        expires_delta=access_token_expires
    )
    
    return {
        "access_token": access_token,
        "token_type": "bearer",
        "expires_in": ACCESS_TOKEN_EXPIRE_MINUTES * 60,
        "user": db_user
    }

@app.get("/auth/me", response_model=UserResponse)
def get_current_user_info(current_user: User = Depends(get_current_active_user)):
    """Get current user information"""
    return current_user

# Admin endpoints for user management
@app.get("/admin/users", response_model=List[UserResponse])
def list_users(
    skip: int = 0, 
    limit: int = 100, 
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin)
):
    """List all users (admin only)"""
    users = db.query(User).offset(skip).limit(limit).all()
    return users

@app.put("/admin/users/{user_id}/role")
def update_user_role(
    user_id: int, 
    role: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin)
):
    """Update user role (admin only)"""
    if role not in ["viewer", "creator", "admin"]:
        raise HTTPException(status_code=400, detail="Invalid role")
    
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    user.role = role
    db.commit()
    return {"message": f"User role updated to {role}"}

# Workflow CRUD endpoints
@app.post("/workflows", response_model=WorkflowResponse)
def create_workflow(
    workflow: WorkflowCreate, 
    db: Session = Depends(get_db),
    current_user: User = Depends(require_creator_or_admin)
):
    """Create a new workflow"""
    # Convert nodes and edges to dictionaries if they're objects
    nodes_data = []
    for node in workflow.nodes:
        if hasattr(node, 'dict'):
            nodes_data.append(node.dict())
        else:
            nodes_data.append(dict(node) if hasattr(node, '__dict__') else node)
    
    edges_data = []
    for edge in workflow.edges:
        if hasattr(edge, 'dict'):
            edges_data.append(edge.dict())
        else:
            edges_data.append(dict(edge) if hasattr(edge, '__dict__') else edge)
    
    db_workflow = Workflow(
        name=workflow.name,
        description=workflow.description,
        nodes=nodes_data,
        edges=edges_data,
        owner_id=current_user.id
    )
    db.add(db_workflow)
    db.commit()
    db.refresh(db_workflow)
    return db_workflow

@app.get("/workflows", response_model=List[WorkflowResponse])
def list_workflows(
    skip: int = 0, 
    limit: int = 100, 
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """List workflows accessible to the current user"""
    if current_user.has_role("admin"):
        # Admin can see all workflows
        workflows = db.query(Workflow).offset(skip).limit(limit).all()
    else:
        # Regular users can see their own workflows, public workflows, and workflows shared with them
        from sqlalchemy import or_
        workflows = db.query(Workflow).join(
            WorkflowShare, 
            (WorkflowShare.workflow_id == Workflow.id) & (WorkflowShare.user_id == current_user.id),
            isouter=True
        ).filter(
            or_(
                Workflow.owner_id == current_user.id,
                Workflow.is_public == True,
                WorkflowShare.id.isnot(None)
            )
        ).distinct().offset(skip).limit(limit).all()
    return workflows

@app.get("/workflows/{workflow_id}", response_model=WorkflowResponse)
def get_workflow(
    workflow_id: int, 
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Get a specific workflow by ID"""
    workflow = check_workflow_permission(workflow_id, "view", current_user, db)
    return workflow

@app.put("/workflows/{workflow_id}", response_model=WorkflowResponse)
def update_workflow(
    workflow_id: int, 
    workflow: WorkflowCreate, 
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Update a workflow"""
    db_workflow = check_workflow_permission(workflow_id, "edit", current_user, db)
    
    # Convert nodes and edges to dictionaries if they're objects
    nodes_data = []
    for node in workflow.nodes:
        if hasattr(node, 'dict'):
            nodes_data.append(node.dict())
        else:
            nodes_data.append(dict(node) if hasattr(node, '__dict__') else node)
    
    edges_data = []
    for edge in workflow.edges:
        if hasattr(edge, 'dict'):
            edges_data.append(edge.dict())
        else:
            edges_data.append(dict(edge) if hasattr(edge, '__dict__') else edge)
    
    db_workflow.name = workflow.name
    db_workflow.description = workflow.description
    db_workflow.nodes = nodes_data
    db_workflow.edges = edges_data
    
    db.commit()
    db.refresh(db_workflow)
    return db_workflow

@app.delete("/workflows/{workflow_id}")
def delete_workflow(
    workflow_id: int, 
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Delete a workflow"""
    db_workflow = check_workflow_permission(workflow_id, "edit", current_user, db)
    
    db.delete(db_workflow)
    db.commit()
    return {"message": "Workflow deleted successfully"}

# Workflow Sharing endpoints
@app.post("/workflows/{workflow_id}/share", response_model=WorkflowShareResponse)
def share_workflow(
    workflow_id: int,
    share_request: WorkflowShareCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Share a workflow with a user"""
    # Check if user has permission to share (owner or admin)
    workflow = db.query(Workflow).filter(Workflow.id == workflow_id).first()
    if not workflow:
        raise HTTPException(status_code=404, detail="Workflow not found")
    
    # Only workflow owner or admin can share
    if workflow.owner_id != current_user.id and not current_user.has_role("admin"):
        raise HTTPException(status_code=403, detail="Not authorized to share this workflow")
    
    # Validate permission level
    if share_request.permission_level not in ["view", "edit"]:
        raise HTTPException(status_code=400, detail="Permission level must be 'view' or 'edit'")
    
    # Check if user exists
    target_user = db.query(User).filter(User.id == share_request.user_id).first()
    if not target_user:
        raise HTTPException(status_code=404, detail="User not found")
    
    # Check if user is trying to share with themselves
    if target_user.id == current_user.id:
        raise HTTPException(status_code=400, detail="Cannot share workflow with yourself")
    
    # Check if share already exists
    existing_share = db.query(WorkflowShare).filter(
        WorkflowShare.workflow_id == workflow_id,
        WorkflowShare.user_id == share_request.user_id
    ).first()
    
    if existing_share:
        # Update existing share
        existing_share.permission_level = share_request.permission_level
        existing_share.updated_at = datetime.utcnow()
        db.commit()
        db.refresh(existing_share)
        return existing_share
    
    # Create new share
    workflow_share = WorkflowShare(
        workflow_id=workflow_id,
        user_id=share_request.user_id,
        permission_level=share_request.permission_level
    )
    db.add(workflow_share)
    db.commit()
    db.refresh(workflow_share)
    return workflow_share

@app.get("/workflows/{workflow_id}/share", response_model=List[WorkflowCollaboratorResponse])
def list_workflow_collaborators(
    workflow_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """List all collaborators for a workflow"""
    workflow = db.query(Workflow).filter(Workflow.id == workflow_id).first()
    if not workflow:
        raise HTTPException(status_code=404, detail="Workflow not found")
    
    # Check if user has permission to view collaborators (owner, admin, or shared user)
    if workflow.owner_id != current_user.id and not current_user.has_role("admin"):
        # Check if user has any share access
        user_share = db.query(WorkflowShare).filter(
            WorkflowShare.workflow_id == workflow_id,
            WorkflowShare.user_id == current_user.id
        ).first()
        if not user_share:
            raise HTTPException(status_code=403, detail="Not authorized to view collaborators")
    
    # Get all shares for this workflow
    shares = db.query(WorkflowShare).filter(WorkflowShare.workflow_id == workflow_id).all()
    
    collaborators = []
    for share in shares:
        collaborator = WorkflowCollaboratorResponse(
            id=share.user.id,
            username=share.user.username,
            email=share.user.email,
            full_name=share.user.full_name,
            role=share.user.role,
            permission_level=share.permission_level,
            shared_at=share.created_at
        )
        collaborators.append(collaborator)
    
    return collaborators

@app.put("/workflows/{workflow_id}/share/{user_id}", response_model=WorkflowShareResponse)
def update_workflow_share(
    workflow_id: int,
    user_id: int,
    share_update: WorkflowShareUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Update a user's permission for a workflow"""
    # Check if user has permission to update shares (owner or admin)
    workflow = db.query(Workflow).filter(Workflow.id == workflow_id).first()
    if not workflow:
        raise HTTPException(status_code=404, detail="Workflow not found")
    
    if workflow.owner_id != current_user.id and not current_user.has_role("admin"):
        raise HTTPException(status_code=403, detail="Not authorized to update workflow shares")
    
    # Validate permission level
    if share_update.permission_level not in ["view", "edit"]:
        raise HTTPException(status_code=400, detail="Permission level must be 'view' or 'edit'")
    
    # Find the share
    workflow_share = db.query(WorkflowShare).filter(
        WorkflowShare.workflow_id == workflow_id,
        WorkflowShare.user_id == user_id
    ).first()
    
    if not workflow_share:
        raise HTTPException(status_code=404, detail="Share not found")
    
    # Update the share
    workflow_share.permission_level = share_update.permission_level
    workflow_share.updated_at = datetime.utcnow()
    db.commit()
    db.refresh(workflow_share)
    return workflow_share

@app.delete("/workflows/{workflow_id}/share/{user_id}")
def delete_workflow_share(
    workflow_id: int,
    user_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Remove a user from workflow collaborators"""
    # Check if user has permission to remove shares (owner or admin)
    workflow = db.query(Workflow).filter(Workflow.id == workflow_id).first()
    if not workflow:
        raise HTTPException(status_code=404, detail="Workflow not found")
    
    if workflow.owner_id != current_user.id and not current_user.has_role("admin"):
        raise HTTPException(status_code=403, detail="Not authorized to remove workflow shares")
    
    # Find the share
    workflow_share = db.query(WorkflowShare).filter(
        WorkflowShare.workflow_id == workflow_id,
        WorkflowShare.user_id == user_id
    ).first()
    
    if not workflow_share:
        raise HTTPException(status_code=404, detail="Share not found")
    
    db.delete(workflow_share)
    db.commit()
    return {"message": "Collaborator removed successfully"}

# Workflow execution endpoints
@app.post("/workflows/{workflow_id}/execute", response_model=WorkflowRunResponse)
def execute_workflow(
    workflow_id: int,
    execution_request: WorkflowExecutionRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Execute a workflow"""
    workflow = check_workflow_permission(workflow_id, "view", current_user, db)
    
    try:
        # Execute the workflow
        import asyncio
        result = asyncio.run(workflow_runner.execute_workflow(workflow.nodes, workflow.edges, execution_request.input_data))
        
        # Create workflow run record
        workflow_run = WorkflowRun(
            workflow_id=workflow_id,
            status="completed",
            result=result,
            logs=workflow_runner.get_logs()
        )
        
        db.add(workflow_run)
        db.commit()
        db.refresh(workflow_run)
        
        # Create execution log entry
        execution_log = WorkflowExecutionLog(
            workflow_id=workflow_id,
            schedule_id=None,  # Manual execution
            status="success",
            input_data=execution_request.input_data,
            output_data=result,
            error_message=None
        )
        db.add(execution_log)
        db.commit()
        
        return workflow_run
        
    except Exception as e:
        # Create failed workflow run record
        workflow_run = WorkflowRun(
            workflow_id=workflow_id,
            status="failed",
            result={"error": str(e)},
            logs=workflow_runner.get_logs()
        )
        
        db.add(workflow_run)
        db.commit()
        db.refresh(workflow_run)
        
        # Create execution log entry for failed execution
        execution_log = WorkflowExecutionLog(
            workflow_id=workflow_id,
            schedule_id=None,  # Manual execution
            status="error",
            input_data=execution_request.input_data,
            output_data=None,
            error_message=str(e)
        )
        db.add(execution_log)
        db.commit()
        
        raise HTTPException(status_code=500, detail=f"Workflow execution failed: {str(e)}")

@app.get("/workflows/{workflow_id}/runs", response_model=List[WorkflowRunResponse])
def list_workflow_runs(
    workflow_id: int, 
    skip: int = 0, 
    limit: int = 100, 
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """List all runs for a specific workflow"""
    workflow = check_workflow_permission(workflow_id, "view", current_user, db)
    
    runs = db.query(WorkflowRun).filter(WorkflowRun.workflow_id == workflow_id)\
        .order_by(WorkflowRun.created_at.desc()).offset(skip).limit(limit).all()
    return runs

@app.get("/workflow_runs/{run_id}", response_model=WorkflowRunResponse)
def get_workflow_run(
    run_id: int, 
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Get a specific workflow run by ID"""
    run = db.query(WorkflowRun).filter(WorkflowRun.id == run_id).first()
    if not run:
        raise HTTPException(status_code=404, detail="Workflow run not found")
    
    # Check permission for the workflow this run belongs to
    check_workflow_permission(run.workflow_id, "view", current_user, db)
    return run

# Workflow Scheduling endpoints
@app.post("/workflows/{workflow_id}/schedules", response_model=WorkflowScheduleResponse)
def create_workflow_schedule(
    workflow_id: int, 
    schedule: WorkflowScheduleCreate, 
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Create a new schedule for a workflow"""
    workflow = check_workflow_permission(workflow_id, "edit", current_user, db)
    
    # Validate cron expression
    if not validate_cron_expression(schedule.cron_expression):
        raise HTTPException(status_code=400, detail="Invalid cron expression")
    
    db_schedule = WorkflowSchedule(
        workflow_id=workflow_id,
        name=schedule.name,
        cron_expression=schedule.cron_expression,
        is_active=schedule.is_active,
        input_data=schedule.input_data,
        owner_id=current_user.id
    )
    db.add(db_schedule)
    db.commit()
    db.refresh(db_schedule)
    
    # Add to scheduler if active
    if schedule.is_active:
        add_schedule_job(db_schedule)
    
    return db_schedule

@app.get("/workflows/{workflow_id}/schedules", response_model=List[WorkflowScheduleResponse])
def list_workflow_schedules(
    workflow_id: int, 
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """List all schedules for a specific workflow"""
    workflow = check_workflow_permission(workflow_id, "view", current_user, db)
    
    schedules = db.query(WorkflowSchedule).filter(WorkflowSchedule.workflow_id == workflow_id).all()
    return schedules

@app.put("/schedules/{schedule_id}", response_model=WorkflowScheduleResponse)
def update_workflow_schedule(
    schedule_id: int, 
    schedule: WorkflowScheduleCreate, 
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Update a workflow schedule"""
    db_schedule = db.query(WorkflowSchedule).filter(WorkflowSchedule.id == schedule_id).first()
    if not db_schedule:
        raise HTTPException(status_code=404, detail="Schedule not found")
    
    # Check permission for the workflow this schedule belongs to
    check_workflow_permission(db_schedule.workflow_id, "edit", current_user, db)
    
    # Validate cron expression
    if not validate_cron_expression(schedule.cron_expression):
        raise HTTPException(status_code=400, detail="Invalid cron expression")
    
    # Remove existing job if it exists
    remove_schedule_job(schedule_id)
    
    db_schedule.name = schedule.name
    db_schedule.cron_expression = schedule.cron_expression
    db_schedule.is_active = schedule.is_active
    db_schedule.input_data = schedule.input_data
    
    db.commit()
    db.refresh(db_schedule)
    
    # Add to scheduler if active
    if schedule.is_active:
        add_schedule_job(db_schedule)
    
    return db_schedule

@app.delete("/schedules/{schedule_id}")
def delete_workflow_schedule(
    schedule_id: int, 
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Delete a workflow schedule"""
    schedule = db.query(WorkflowSchedule).filter(WorkflowSchedule.id == schedule_id).first()
    if not schedule:
        raise HTTPException(status_code=404, detail="Schedule not found")
    
    # Check permission for the workflow this schedule belongs to
    check_workflow_permission(schedule.workflow_id, "edit", current_user, db)
    
    # Remove from scheduler
    remove_schedule_job(schedule_id)
    
    db.delete(schedule)
    db.commit()
    return {"message": "Schedule deleted successfully"}

@app.post("/schedules/{schedule_id}/toggle")
def toggle_workflow_schedule(
    schedule_id: int, 
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Toggle a schedule between active and inactive"""
    schedule = db.query(WorkflowSchedule).filter(WorkflowSchedule.id == schedule_id).first()
    if not schedule:
        raise HTTPException(status_code=404, detail="Schedule not found")
    
    # Check permission for the workflow this schedule belongs to
    check_workflow_permission(schedule.workflow_id, "edit", current_user, db)
    
    # Toggle the status
    schedule.is_active = 1 if schedule.is_active == 0 else 0
    db.commit()
    
    # Update scheduler
    if schedule.is_active:
        add_schedule_job(schedule)
    else:
        remove_schedule_job(schedule_id)
    
    return {"message": f"Schedule {'activated' if schedule.is_active else 'deactivated'} successfully"}

# Scheduler helper functions
def execute_scheduled_workflow(schedule_id: int, workflow_id: int, input_data: dict):
    """Execute a workflow as part of a scheduled job"""
    db = next(get_db())
    try:
        workflow = db.query(Workflow).filter(Workflow.id == workflow_id).first()
        if not workflow:
            print(f"Workflow {workflow_id} not found for schedule {schedule_id}")
            return
        
        # Execute the workflow
        import asyncio
        result = asyncio.run(workflow_runner.execute_workflow(workflow.nodes, workflow.edges, input_data))
        
        # Create workflow run record
        workflow_run = WorkflowRun(
            workflow_id=workflow_id,
            status="completed",
            result=result,
            logs=workflow_runner.get_logs()
        )
        
        db.add(workflow_run)
        db.commit()
        
        # Create execution log entry for successful execution
        execution_log = WorkflowExecutionLog(
            workflow_id=workflow_id,
            schedule_id=schedule_id,
            status="success",
            input_data=input_data,
            output_data=result,
            error_message=None
        )
        db.add(execution_log)
        db.commit()
        
        print(f"Scheduled workflow {workflow_id} executed successfully")
        
    except Exception as e:
        print(f"Error executing scheduled workflow {workflow_id}: {str(e)}")
        # Create failed workflow run record
        workflow_run = WorkflowRun(
            workflow_id=workflow_id,
            status="failed",
            result={"error": str(e)},
            logs=workflow_runner.get_logs()
        )
        
        db.add(workflow_run)
        db.commit()
        
        # Create execution log entry for failed execution
        execution_log = WorkflowExecutionLog(
            workflow_id=workflow_id,
            schedule_id=schedule_id,
            status="error",
            input_data=input_data,
            output_data=None,
            error_message=str(e)
        )
        db.add(execution_log)
        db.commit()
    finally:
        db.close()

def validate_cron_expression(cron_expr: str) -> bool:
    """Validate a cron expression"""
    try:
        croniter(cron_expr)
        return True
    except Exception:
        return False

def add_schedule_job(schedule: WorkflowSchedule):
    """Add a schedule job to the scheduler"""
    if not schedule.is_active:
        return
    
    if not validate_cron_expression(schedule.cron_expression):
        print(f"Invalid cron expression for schedule {schedule.id}: {schedule.cron_expression}")
        return
    
    try:
        job = scheduler.add_job(
            execute_scheduled_workflow,
            trigger=CronTrigger.from_crontab(schedule.cron_expression),
            id=f"schedule_{schedule.id}",
            args=[schedule.id, schedule.workflow_id, schedule.input_data or {}],
            replace_existing=True
        )
        scheduled_jobs[schedule.id] = job
        print(f"Added schedule job for schedule {schedule.id}")
    except Exception as e:
        print(f"Error adding schedule job for schedule {schedule.id}: {str(e)}")

def remove_schedule_job(schedule_id: int):
    """Remove a schedule job from the scheduler"""
    try:
        job_id = f"schedule_{schedule_id}"
        if scheduler.get_job(job_id):
            scheduler.remove_job(job_id)
        if schedule_id in scheduled_jobs:
            del scheduled_jobs[schedule_id]
        print(f"Removed schedule job for schedule {schedule_id}")
    except Exception as e:
        print(f"Error removing schedule job for schedule {schedule_id}: {str(e)}")

def load_existing_schedules():
    """Load existing schedules on startup"""
    db = next(get_db())
    try:
        # Check if the workflow_schedules table exists and has the owner_id column
        from sqlalchemy import inspect
        inspector = inspect(db.bind)
        
        # Check if table exists
        if 'workflow_schedules' not in inspector.get_table_names():
            print("workflow_schedules table does not exist yet, skipping schedule loading")
            return
            
        # Check if owner_id column exists
        columns = [col['name'] for col in inspector.get_columns('workflow_schedules')]
        if 'owner_id' not in columns:
            print("owner_id column does not exist in workflow_schedules table, skipping schedule loading")
            return
            
        schedules = db.query(WorkflowSchedule).filter(WorkflowSchedule.is_active == True).all()
        for schedule in schedules:
            add_schedule_job(schedule)
        print(f"Loaded {len(schedules)} active schedules")
    except Exception as e:
        print(f"Error loading existing schedules: {str(e)}")
    finally:
        db.close()

# Workflow Execution Log endpoints
@app.get("/workflows/{workflow_id}/logs", response_model=List[WorkflowExecutionLogResponse])
def list_workflow_execution_logs(
    workflow_id: int, 
    skip: int = 0, 
    limit: int = 100, 
    status: Optional[str] = None,
    start_date: Optional[datetime] = None,
    end_date: Optional[datetime] = None,
    schedule_id: Optional[int] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """List execution logs for a specific workflow with optional filtering"""
    workflow = check_workflow_permission(workflow_id, "view", current_user, db)
    
    query = db.query(WorkflowExecutionLog).filter(WorkflowExecutionLog.workflow_id == workflow_id)
    
    # Apply filters
    if status:
        query = query.filter(WorkflowExecutionLog.status == status)
    if start_date:
        query = query.filter(WorkflowExecutionLog.execution_time >= start_date)
    if end_date:
        query = query.filter(WorkflowExecutionLog.execution_time <= end_date)
    if schedule_id:
        query = query.filter(WorkflowExecutionLog.schedule_id == schedule_id)
    
    logs = query.order_by(WorkflowExecutionLog.execution_time.desc()).offset(skip).limit(limit).all()
    return logs

@app.get("/logs/{log_id}", response_model=WorkflowExecutionLogResponse)
def get_execution_log(
    log_id: int, 
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Get a specific execution log by ID"""
    log = db.query(WorkflowExecutionLog).filter(WorkflowExecutionLog.id == log_id).first()
    if not log:
        raise HTTPException(status_code=404, detail="Execution log not found")
    
    # Check permission for the workflow this log belongs to
    check_workflow_permission(log.workflow_id, "view", current_user, db)
    return log

@app.delete("/logs/{log_id}")
def delete_execution_log(
    log_id: int, 
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Delete an execution log"""
    log = db.query(WorkflowExecutionLog).filter(WorkflowExecutionLog.id == log_id).first()
    if not log:
        raise HTTPException(status_code=404, detail="Execution log not found")
    
    # Check permission for the workflow this log belongs to
    check_workflow_permission(log.workflow_id, "edit", current_user, db)
    
    db.delete(log)
    db.commit()
    return {"message": "Execution log deleted successfully"}

# Plugin endpoints
@app.get("/plugins")
def list_plugins(current_user: User = Depends(get_current_active_user)):
    """List all available plugins"""
    plugins = plugin_manager.list_plugins()
    plugin_info = []
    
    for plugin_id in plugins:
        metadata = plugin_manager.get_plugin_metadata(plugin_id)
        if metadata:
            plugin_info.append({
                "plugin_id": metadata["plugin_id"],
                "name": metadata["name"],
                "description": metadata["description"],
                "version": metadata["version"],
                "author": metadata["author"]
            })
    
    return {"plugins": plugin_info}

@app.get("/plugins/{plugin_id}")
def get_plugin_details(
    plugin_id: str, 
    current_user: User = Depends(get_current_active_user)
):
    """Get detailed information about a specific plugin"""
    metadata = plugin_manager.get_plugin_metadata(plugin_id)
    if not metadata:
        raise HTTPException(status_code=404, detail="Plugin not found")
    
    return metadata

@app.post("/plugins/{plugin_id}/execute")
def execute_plugin(
    plugin_id: str,
    input_data: dict,
    current_user: User = Depends(get_current_active_user)
):
    """Execute a plugin with the provided input data"""
    result = plugin_manager.execute_plugin(plugin_id, input_data)
    
    if not result.get("success", False):
        raise HTTPException(status_code=400, detail=result.get("error", "Plugin execution failed"))
    
    return result

@app.post("/plugins/{plugin_id}/config")
def update_plugin_config(
    plugin_id: str,
    config: dict,
    current_user: User = Depends(require_admin)
):
    """Update plugin configuration (admin only)"""
    plugin_manager.set_plugin_config(plugin_id, config)
    return {"message": f"Configuration updated for plugin {plugin_id}"}

@app.get("/plugins/{plugin_id}/config")
def get_plugin_config(
    plugin_id: str,
    current_user: User = Depends(require_admin)
):
    """Get plugin configuration (admin only)"""
    config = plugin_manager.get_plugin_config(plugin_id)
    return {"plugin_id": plugin_id, "config": config}

# Workflow Export/Import endpoints
@app.get("/workflows/{workflow_id}/export")
def export_workflow(
    workflow_id: int,
    format: str = "json",
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Export a workflow in JSON or ZIP format"""
    workflow = check_workflow_permission(workflow_id, "view", current_user, db)
    
    if format not in ["json", "zip"]:
        raise HTTPException(status_code=400, detail="Format must be 'json' or 'zip'")
    
    # Prepare export data
    export_data = {
        "version": "1.0",
        "exported_at": datetime.utcnow().isoformat(),
        "workflow": {
            "name": workflow.name,
            "description": workflow.description,
            "nodes": workflow.nodes,
            "edges": workflow.edges,
            "is_public": workflow.is_public,
            "created_at": workflow.created_at.isoformat() if workflow.created_at else None,
            "updated_at": workflow.updated_at.isoformat() if workflow.updated_at else None
        },
        "metadata": {
            "exported_by": current_user.username,
            "workflow_id": workflow.id,
            "owner": {
                "username": workflow.owner.username,
                "email": workflow.owner.email
            }
        }
    }
    
    if format == "json":
        # Return as JSON file
        json_content = json.dumps(export_data, indent=2, default=str)
        return StreamingResponse(
            io.BytesIO(json_content.encode()),
            media_type="application/json",
            headers={
                "Content-Disposition": f"attachment; filename=workflow_{workflow.name.replace(' ', '_')}_{workflow_id}.json"
            }
        )
    else:  # zip format
        # Create ZIP file with JSON and metadata
        zip_buffer = io.BytesIO()
        with zipfile.ZipFile(zip_buffer, 'w', zipfile.ZIP_DEFLATED) as zip_file:
            # Add main workflow JSON
            zip_file.writestr(
                f"workflow_{workflow.name.replace(' ', '_')}.json",
                json.dumps(export_data, indent=2, default=str)
            )
            
            # Add README with import instructions
            readme_content = f"""# Workflow Export

This ZIP file contains a workflow exported from WorkFlowN2N.

## Import Instructions

1. Log into your WorkFlowN2N instance
2. Navigate to the workflow import page
3. Upload this ZIP file or the contained JSON file
4. Review and customize the imported workflow

## Workflow Details
- Name: {workflow.name}
- Description: {workflow.description or 'No description'}
- Exported by: {current_user.username}
- Exported at: {datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S UTC')}

## Notes
- Node configurations and connections are preserved
- Plugin configurations are included
- You may need to reconfigure API keys or external service connections after import
"""
            zip_file.writestr("README.md", readme_content)
        
        zip_buffer.seek(0)
        return StreamingResponse(
            zip_buffer,
            media_type="application/zip",
            headers={
                "Content-Disposition": f"attachment; filename=workflow_{workflow.name.replace(' ', '_')}_{workflow_id}.zip"
            }
        )

@app.post("/workflows/import", response_model=WorkflowResponse)
def import_workflow(
    file: UploadFile = File(...),
    name: Optional[str] = None,
    description: Optional[str] = None,
    make_public: bool = False,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Import a workflow from JSON or ZIP file"""
    # Check if user can create workflows
    if not current_user.has_role("creator") and not current_user.has_role("admin"):
        raise HTTPException(status_code=403, detail="Not authorized to create workflows")
    
    # Validate file type
    if not file.content_type:
        # Try to infer from filename
        if file.filename.endswith('.json'):
            file.content_type = 'application/json'
        elif file.filename.endswith('.zip'):
            file.content_type = 'application/zip'
        else:
            raise HTTPException(status_code=400, detail="Unable to determine file type")
    
    if file.content_type not in ["application/json", "application/zip", "application/x-zip-compressed"]:
        raise HTTPException(status_code=400, detail="File must be JSON or ZIP format")
    
    try:
        # Read file content
        content = file.file.read()
        
        if file.content_type in ["application/zip", "application/x-zip-compressed"]:
            # Handle ZIP file
            zip_buffer = io.BytesIO(content)
            with zipfile.ZipFile(zip_buffer, 'r') as zip_file:
                # Find the main JSON file (should be the only JSON file)
                json_files = [name for name in zip_file.namelist() if name.endswith('.json')]
                if not json_files:
                    raise HTTPException(status_code=400, detail="No JSON file found in ZIP archive")
                
                # Use the first JSON file found
                json_content = zip_file.read(json_files[0]).decode('utf-8')
                import_data = json.loads(json_content)
        else:
            # Handle JSON file
            import_data = json.loads(content.decode('utf-8'))
        
        # Validate import data structure
        if not isinstance(import_data, dict):
            raise HTTPException(status_code=400, detail="Invalid file format")
        
        # Check version compatibility
        version = import_data.get("version", "1.0")
        if version not in ["1.0"]:
            raise HTTPException(status_code=400, detail=f"Unsupported version: {version}")
        
        # Extract workflow data
        workflow_data = import_data.get("workflow")
        if not workflow_data:
            raise HTTPException(status_code=400, detail="No workflow data found in import file")
        
        # Validate required fields
        required_fields = ["name", "nodes", "edges"]
        for field in required_fields:
            if field not in workflow_data:
                raise HTTPException(status_code=400, detail=f"Missing required field: {field}")
        
        # Validate nodes and edges structure
        if not isinstance(workflow_data["nodes"], list):
            raise HTTPException(status_code=400, detail="Invalid nodes format")
        if not isinstance(workflow_data["edges"], list):
            raise HTTPException(status_code=400, detail="Invalid edges format")
        
        # Create new workflow
        new_workflow = Workflow(
            name=name or workflow_data["name"],
            description=description or workflow_data.get("description", ""),
            nodes=workflow_data["nodes"],
            edges=workflow_data["edges"],
            owner_id=current_user.id,
            is_public=make_public
        )
        
        db.add(new_workflow)
        db.commit()
        db.refresh(new_workflow)
        
        return new_workflow
        
    except json.JSONDecodeError as e:
        raise HTTPException(status_code=400, detail=f"Invalid JSON format: {str(e)}")
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=400, detail=f"Import failed: {str(e)}")

@app.post("/workflows/bulk-export")
def bulk_export_workflows(
    workflow_ids: List[int],
    format: str = "zip",
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Export multiple workflows as a single ZIP file"""
    if format != "zip":
        raise HTTPException(status_code=400, detail="Bulk export only supports ZIP format")
    
    if not workflow_ids:
        raise HTTPException(status_code=400, detail="No workflow IDs provided")
    
    # Check permissions and collect workflows
    workflows = []
    for workflow_id in workflow_ids:
        try:
            workflow = check_workflow_permission(workflow_id, "view", current_user, db)
            workflows.append(workflow)
        except HTTPException:
            # Skip workflows user doesn't have access to
            continue
    
    if not workflows:
        raise HTTPException(status_code=404, detail="No accessible workflows found")
    
    # Create ZIP file
    zip_buffer = io.BytesIO()
    with zipfile.ZipFile(zip_buffer, 'w', zipfile.ZIP_DEFLATED) as zip_file:
        # Add each workflow
        for workflow in workflows:
            export_data = {
                "version": "1.0",
                "exported_at": datetime.utcnow().isoformat(),
                "workflow": {
                    "name": workflow.name,
                    "description": workflow.description,
                    "nodes": workflow.nodes,
                    "edges": workflow.edges,
                    "is_public": workflow.is_public,
                    "created_at": workflow.created_at.isoformat() if workflow.created_at else None,
                    "updated_at": workflow.updated_at.isoformat() if workflow.updated_at else None
                },
                "metadata": {
                    "exported_by": current_user.username,
                    "workflow_id": workflow.id,
                    "owner": {
                        "username": workflow.owner.username,
                        "email": workflow.owner.email
                    }
                }
            }
            
            # Create safe filename
            safe_name = workflow.name.replace(' ', '_').replace('/', '_').replace('\\', '_')
            zip_file.writestr(
                f"{safe_name}_{workflow.id}.json",
                json.dumps(export_data, indent=2, default=str)
            )
        
        # Add manifest file
        manifest = {
            "version": "1.0",
            "exported_at": datetime.utcnow().isoformat(),
            "exported_by": current_user.username,
            "total_workflows": len(workflows),
            "workflows": [
                {
                    "id": w.id,
                    "name": w.name,
                    "description": w.description,
                    "owner": w.owner.username
                }
                for w in workflows
            ]
        }
        zip_file.writestr("manifest.json", json.dumps(manifest, indent=2))
        
        # Add README
        readme_content = f"""# Bulk Workflow Export

This ZIP file contains {len(workflows)} workflows exported from WorkFlowN2N.

## Import Instructions

1. Extract individual workflow JSON files from this archive
2. Import each workflow using the WorkFlowN2N import feature
3. Review and customize the imported workflows as needed

## Exported Workflows

{chr(10).join(f"- {w.name} (ID: {w.id})" for w in workflows)}

## Notes
- Node configurations and connections are preserved
- Plugin configurations are included
- You may need to reconfigure API keys or external service connections after import
"""
        zip_file.writestr("README.md", readme_content)
    
    zip_buffer.seek(0)
    return StreamingResponse(
        zip_buffer,
        media_type="application/zip",
        headers={
            "Content-Disposition": f"attachment; filename=workflows_bulk_export_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}.zip"
        }
    )

if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)