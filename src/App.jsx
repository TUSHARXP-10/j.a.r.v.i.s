import React, { useRef, useCallback, useState, useEffect } from 'react';
import * as RF from '@xyflow/react';
const { ReactFlow, ReactFlowProvider, addEdge, useNodesState, useEdgesState, Controls, Background, useReactFlow } = RF;
import '@xyflow/react/dist/style.css';
import './App.css';
import { InputNode, ActionNode, HttpNode, FileNode, DatabaseNode, ConditionNode, DelayNode, OutputNode } from './CustomNodes';
import { exportWorkflow, downloadWorkflow, loadWorkflowFromFile } from './workflowUtils';
import { workflowAPI } from './api';
import { authAPI } from './services/authAPI';
import { AuthProvider, useAuth } from './contexts/AuthContext';
import Navigation from './components/Navigation';
import LoginForm from './components/LoginForm';
import RegisterForm from './components/RegisterForm';
import UserManagement from './components/UserManagement';
import ScheduleModal from './components/ScheduleModal';
import ExecutionLogs from './components/ExecutionLogs';
import WorkflowSharing from './components/WorkflowSharing';
import Toolbar from './components/Toolbar';
import PluginNode from './components/PluginNode';
import PluginSelector from './components/PluginSelector';
import WorkflowImportExport from './components/WorkflowImportExport';

const nodeTypes = {
  input: InputNode,
  default: ActionNode,
  http: HttpNode,
  file: FileNode,
  database: DatabaseNode,
  condition: ConditionNode,
  delay: DelayNode,
  output: OutputNode,
  plugin: PluginNode,
};

const initialNodes = [
  { id: '1', type: 'input', data: { label: 'Input Node' }, position: { x: 100, y: 50 } }
];

let id = 2;
const getId = () => `dndnode_${id++}`;

export default function App() {
  return (
    <AuthProvider>
      <WorkflowApp />
    </AuthProvider>
  );
}

function Sidebar() {
  const onDragStart = (event, nodeType) => {
    event.dataTransfer.setData('application/reactflow', nodeType);
    event.dataTransfer.effectAllowed = 'move';
  };

  const handlePluginDragStart = (event) => {
    event.dataTransfer.setData('application/reactflow', 'plugin');
    event.dataTransfer.effectAllowed = 'move';
  };

  return (
    <div className="sidebar">
      <h3>Node Types</h3>
      <div 
        className="node-item input-node" 
        onDragStart={(event) => onDragStart(event, 'input')}
        draggable
      >
        Input Node
      </div>
      <div 
        className="node-item action-node" 
        onDragStart={(event) => onDragStart(event, 'default')}
        draggable
      >
        Action Node
      </div>
      <div 
        className="node-item http-node" 
        onDragStart={(event) => onDragStart(event, 'http')}
        draggable
      >
        HTTP Request
      </div>
      <div 
        className="node-item file-node" 
        onDragStart={(event) => onDragStart(event, 'file')}
        draggable
      >
        File Operation
      </div>
      <div 
        className="node-item database-node" 
        onDragStart={(event) => onDragStart(event, 'database')}
        draggable
      >
        Database
      </div>
      <div 
        className="node-item condition-node" 
        onDragStart={(event) => onDragStart(event, 'condition')}
        draggable
      >
        Condition
      </div>
      <div 
        className="node-item delay-node" 
        onDragStart={(event) => onDragStart(event, 'delay')}
        draggable
      >
        Delay
      </div>
      <div 
        className="node-item output-node" 
        onDragStart={(event) => onDragStart(event, 'output')}
        draggable
      >
        Output
      </div>
      <div 
        className="node-item plugin-node" 
        onDragStart={handlePluginDragStart}
        draggable
      >
        Plugin
      </div>
    </div>
  );
}

function FlowCanvas({ 
  workflowName, 
  setWorkflowName, 
  nodes, 
  setNodes, 
  edges, 
  setEdges, 
  onNodesChange, 
  onEdgesChange,
  onSave,
  onExecute,
  isLoading,
  savedWorkflows,
  onLoadWorkflow,
  workflowRuns,
  schedules,
  createSchedule,
  updateSchedule,
  deleteSchedule,
  toggleSchedule,
  onShowExecutionLogs,
  onShowSharing,
  workflowId
}) {
  const reactFlowWrapper = useRef(null);
  const { screenToFlowPosition } = useReactFlow();
  const [showPluginSelector, setShowPluginSelector] = useState(false);
  const [pendingPluginPosition, setPendingPluginPosition] = useState(null);

  const onConnect = useCallback(
    (params) => setEdges((eds) => addEdge(params, eds)), []
  );

  const onDrop = useCallback((event) => {
    event.preventDefault();
    const nodeType = event.dataTransfer.getData('application/reactflow');
    const position = screenToFlowPosition({ x: event.clientX, y: event.clientY });
    
    if (nodeType === 'plugin') {
      // Show plugin selector instead of creating node immediately
      setPendingPluginPosition(position);
      setShowPluginSelector(true);
      return;
    }
    
    const newNode = {
      id: getId(),
      type: nodeType,
      position,
      data: { label: `${nodeType} node` },
    };
    setNodes((nds) => nds.concat(newNode));
  }, [screenToFlowPosition, setNodes]);

  const onDragOver = useCallback((event) => {
    event.preventDefault();
    event.dataTransfer.dropEffect = 'move';
  }, []);

  const handleExport = useCallback(() => {
    const workflow = exportWorkflow(nodes, edges, workflowName || 'Untitled Workflow');
    downloadWorkflow(workflow);
  }, [nodes, edges, workflowName]);

  const handleImport = useCallback((importedNodes, importedEdges) => {
    setNodes(importedNodes);
    setEdges(importedEdges);
  }, [setNodes, setEdges]);

  const handlePluginSelect = useCallback((plugin) => {
    if (!pendingPluginPosition) return;
    
    const newNode = {
      id: getId(),
      type: 'plugin',
      position: pendingPluginPosition,
      data: { 
        label: plugin.name,
        plugin: plugin,
        pluginId: plugin.id,
        config: {}
      },
    };
    setNodes((nds) => nds.concat(newNode));
    setShowPluginSelector(false);
    setPendingPluginPosition(null);
  }, [pendingPluginPosition, setNodes]);

  const handlePluginSelectorClose = useCallback(() => {
    setShowPluginSelector(false);
    setPendingPluginPosition(null);
  }, []);

  return (
    <div className="flow-container">
      <Toolbar 
          onExport={handleExport} 
          onImport={handleImport} 
          workflowName={workflowName}
          setWorkflowName={setWorkflowName}
          onSave={onSave}
          onExecute={onExecute}
          isLoading={isLoading}
          savedWorkflows={savedWorkflows}
          onLoadWorkflow={onLoadWorkflow}
          workflowRuns={workflowRuns}
          schedules={schedules}
          createSchedule={createSchedule}
          updateSchedule={updateSchedule}
          deleteSchedule={deleteSchedule}
          toggleSchedule={toggleSchedule}
          onShowExecutionLogs={onShowExecutionLogs}
          onShowSharing={onShowSharing}
        />
      <WorkflowImportExport 
        workflowId={workflowId}
        workflowName={workflowName}
        nodes={nodes}
        edges={edges}
        onImport={handleImport}
        savedWorkflows={savedWorkflows}
      />
      <div className="canvas-container" ref={reactFlowWrapper}>
        <ReactFlow
          nodes={nodes}
          edges={edges}
          onNodesChange={onNodesChange}
          onEdgesChange={onEdgesChange}
          onConnect={onConnect}
          onDrop={onDrop}
          onDragOver={onDragOver}
          fitView
          nodeTypes={nodeTypes}
        >
          <Controls />
          <Background />
        </ReactFlow>
      </div>
      
      {showPluginSelector && (
        <PluginSelector
          onSelectPlugin={handlePluginSelect}
          onClose={handlePluginSelectorClose}
        />
      )}
    </div>
  );
}

function WorkflowApp() {
  const [workflowName, setWorkflowName] = useState('Untitled Workflow')
  const [workflowId, setWorkflowId] = useState(null)
  const [savedWorkflows, setSavedWorkflows] = useState([])
  const [isLoading, setIsLoading] = useState(false)
  const [error, setError] = useState(null)
  const [workflowRuns, setWorkflowRuns] = useState([])
  const [schedules, setSchedules] = useState([])
  const [showExecutionLogs, setShowExecutionLogs] = useState(false)
  const [showWorkflowSharing, setShowWorkflowSharing] = useState(false)
  const [nodes, setNodes, onNodesChange] = useNodesState([])
  const [edges, setEdges, onEdgesChange] = useEdgesState([])
  const [currentView, setCurrentView] = useState('workflows')

  // Load saved workflows on component mount
  useEffect(() => {
    loadSavedWorkflows()
  }, [])

  const loadSavedWorkflows = async () => {
    try {
      setIsLoading(true)
      setError(null)
      const workflows = await workflowAPI.getWorkflows()
      setSavedWorkflows(workflows)
    } catch (err) {
      setError('Failed to load saved workflows')
      console.error('Error loading workflows:', err)
    } finally {
      setIsLoading(false)
    }
  }

  const loadWorkflow = async (workflowId) => {
    try {
      setIsLoading(true)
      setError(null)
      const workflow = await workflowAPI.getWorkflow(workflowId)
      
      // Update local state with loaded workflow
      setWorkflowName(workflow.name)
      setWorkflowId(workflow.id)
      setNodes(workflow.nodes)
      setEdges(workflow.edges)
      
      // Load workflow runs history
      await loadWorkflowRuns(workflowId)
      
      // Load schedules
      await loadSchedules(workflowId)
      
      return workflow
    } catch (err) {
      setError('Failed to load workflow')
      console.error('Error loading workflow:', err)
      throw err
    } finally {
      setIsLoading(false)
    }
  }

  const saveWorkflow = async () => {
    try {
      setIsLoading(true)
      setError(null)
      
      const workflowData = {
        name: workflowName,
        description: 'Workflow created with visual editor',
        nodes: nodes,
        edges: edges
      }

      let savedWorkflow
      if (workflowId) {
        // Update existing workflow
        savedWorkflow = await workflowAPI.updateWorkflow(workflowId, workflowData)
      } else {
        // Create new workflow
        savedWorkflow = await workflowAPI.createWorkflow(workflowData)
        setWorkflowId(savedWorkflow.id)
      }
      
      // Refresh saved workflows list
      await loadSavedWorkflows()
      
      return savedWorkflow
    } catch (err) {
      setError('Failed to save workflow')
      console.error('Error saving workflow:', err)
      throw err
    } finally {
      setIsLoading(false)
    }
  }

  const executeWorkflow = async (inputData = {}) => {
    try {
      if (!workflowId) {
        throw new Error('Please save the workflow before executing')
      }
      
      setIsLoading(true)
      setError(null)
      
      const result = await workflowAPI.executeWorkflow(workflowId, inputData)
      
      // Refresh workflow runs after execution
      await loadWorkflowRuns(workflowId)
      
      return result
    } catch (err) {
      setError('Failed to execute workflow')
      console.error('Error executing workflow:', err)
      throw err
    } finally {
      setIsLoading(false)
    }
  };

  const loadWorkflowRuns = async (workflowId) => {
    try {
      const runs = await workflowAPI.getWorkflowRuns(workflowId)
      setWorkflowRuns(runs)
    } catch (err) {
      console.error('Error loading workflow runs:', err)
    }
  };

  const loadSchedules = async (workflowId) => {
    try {
      const schedules = await workflowAPI.getSchedules(workflowId)
      setSchedules(schedules)
    } catch (err) {
      console.error('Error loading schedules:', err)
    }
  };

  const createSchedule = async (scheduleData) => {
    try {
      if (!workflowId) {
        throw new Error('Please save the workflow before creating a schedule')
      }
      
      setIsLoading(true)
      setError(null)
      
      const newSchedule = await workflowAPI.createSchedule(workflowId, scheduleData)
      await loadSchedules(workflowId)
      
      return newSchedule
    } catch (err) {
      setError('Failed to create schedule')
      console.error('Error creating schedule:', err)
      throw err
    } finally {
      setIsLoading(false)
    }
  };

  const updateSchedule = async (scheduleId, scheduleData) => {
    try {
      setIsLoading(true)
      setError(null)
      
      const updatedSchedule = await workflowAPI.updateSchedule(scheduleId, scheduleData)
      await loadSchedules(workflowId)
      
      return updatedSchedule
    } catch (err) {
      setError('Failed to update schedule')
      console.error('Error updating schedule:', err)
      throw err
    } finally {
      setIsLoading(false)
    }
  };

  const deleteSchedule = async (scheduleId) => {
    try {
      setIsLoading(true)
      setError(null)
      
      await workflowAPI.deleteSchedule(scheduleId)
      await loadSchedules(workflowId)
    } catch (err) {
      setError('Failed to delete schedule')
      console.error('Error deleting schedule:', err)
      throw err
    } finally {
      setIsLoading(false)
    }
  };

  const toggleSchedule = async (scheduleId) => {
    try {
      setIsLoading(true)
      setError(null)
      
      await workflowAPI.toggleSchedule(scheduleId)
      await loadSchedules(workflowId)
    } catch (err) {
      setError('Failed to toggle schedule')
      console.error('Error toggling schedule:', err)
      throw err
    } finally {
      setIsLoading(false)
    }
  };

  const handleShowExecutionLogs = () => {
    if (!workflowId) {
      setError('Please load or save a workflow first to view execution logs')
      return
    }
    setShowExecutionLogs(true)
  };

  const handleCloseExecutionLogs = () => {
    setShowExecutionLogs(false)
  };

  const handleShowWorkflowSharing = () => {
    if (!workflowId) {
      setError('Please load or save a workflow first to share it')
      return
    }
    setShowWorkflowSharing(true)
  };

  const handleCloseWorkflowSharing = () => {
    setShowWorkflowSharing(false)
  };

  const { user, loading } = useAuth();

  if (loading) {
    return <div className="loading-screen">Loading...</div>;
  }

  if (!user) {
    return (
      <div className="auth-container">
        {currentView === 'login' ? (
          <LoginForm onToggleView={() => setCurrentView('register')} />
        ) : (
          <RegisterForm onToggleView={() => setCurrentView('login')} />
        )}
      </div>
    );
  }

  return (
    <div className="app-container">
      <Navigation currentView={currentView} onViewChange={setCurrentView} />
      
      {currentView === 'users' ? (
        <UserManagement />
      ) : (
        <ReactFlowProvider>
          <div className="workflow-container">
            {/* Error Display */}
            {error && (
              <div className="error-message">
                {error}
                <button onClick={() => setError(null)} className="error-close">×</button>
              </div>
            )}

            <Sidebar />
            <FlowCanvas 
              workflowName={workflowName} 
              setWorkflowName={setWorkflowName} 
              nodes={nodes} 
              setNodes={setNodes}
              edges={edges} 
              setEdges={setEdges}
              onNodesChange={onNodesChange}
              onEdgesChange={onEdgesChange}
              onSave={saveWorkflow}
              onExecute={executeWorkflow}
              isLoading={isLoading}
              savedWorkflows={savedWorkflows}
              onLoadWorkflow={loadWorkflow}
              workflowRuns={workflowRuns}
              schedules={schedules}
              createSchedule={createSchedule}
              updateSchedule={updateSchedule}
              deleteSchedule={deleteSchedule}
              toggleSchedule={toggleSchedule}
              onShowExecutionLogs={handleShowExecutionLogs}
              onShowSharing={handleShowWorkflowSharing}
              workflowId={workflowId}
            />
            
            {showExecutionLogs && (
              <ExecutionLogs 
                workflowId={workflowId}
                onClose={handleCloseExecutionLogs}
              />
            )}
            
            {showWorkflowSharing && (
              <WorkflowSharing 
                workflowId={workflowId}
                onClose={handleCloseWorkflowSharing}
              />
            )}
          </div>
        </ReactFlowProvider>
      )}
    </div>
  );
}
