import React, { useCallback, useRef, useState, useEffect } from 'react';
import ReactFlow, {
  ReactFlowProvider,
  addEdge,
  useNodesState,
  useEdgesState,
  useReactFlow,
  Controls,
  Background,
} from 'reactflow';
import 'reactflow/dist/style.css';
import Toolbar from './Toolbar';
import PluginNode from './PluginNode';
import PluginSelector from './PluginSelector';
import { exportWorkflow, downloadWorkflow, getId } from '../utils/workflowUtils';
import './FlowCanvas.css';

const nodeTypes = {
  plugin: PluginNode,
  default: ({ data }) => (
    <div className="react-flow__node-default">
      <div className="node-header">Action</div>
      <div className="node-content">{data.label}</div>
    </div>
  ),
  input: ({ data }) => (
    <div className="react-flow__node-input">
      <div className="node-header">Input</div>
      <div className="node-content">{data.label}</div>
    </div>
  ),
  output: ({ data }) => (
    <div className="react-flow__node-output">
      <div className="node-header">Output</div>
      <div className="node-content">{data.label}</div>
    </div>
  ),
  http: ({ data }) => (
    <div className="react-flow__node-default">
      <div className="node-header">HTTP Request</div>
      <div className="node-content">{data.label}</div>
    </div>
  ),
  file: ({ data }) => (
    <div className="react-flow__node-default">
      <div className="node-header">File Operation</div>
      <div className="node-content">{data.label}</div>
    </div>
  ),
  database: ({ data }) => (
    <div className="react-flow__node-default">
      <div className="node-header">Database</div>
      <div className="node-content">{data.label}</div>
    </div>
  ),
  condition: ({ data }) => (
    <div className="react-flow__node-default">
      <div className="node-header">Condition</div>
      <div className="node-content">{data.label}</div>
    </div>
  ),
  delay: ({ data }) => (
    <div className="react-flow__node-default">
      <div className="node-header">Delay</div>
      <div className="node-content">{data.label}</div>
    </div>
  ),
};

const onDragStart = (event, nodeType) => {
  event.dataTransfer.setData('application/reactflow', nodeType);
  event.dataTransfer.effectAllowed = 'move';
};

function FlowCanvasContent({ 
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
  onShowSharing
}) {
  const reactFlowWrapper = useRef(null);
  const { screenToFlowPosition } = useReactFlow();
  const [showPluginSelector, setShowPluginSelector] = useState(false);
  const [selectedPluginNode, setSelectedPluginNode] = useState(null);

  const onConnect = useCallback(
    (params) => setEdges((eds) => addEdge(params, eds)), []
  );

  const onDrop = useCallback((event) => {
    event.preventDefault();
    const nodeType = event.dataTransfer.getData('application/reactflow');
    const position = screenToFlowPosition({ x: event.clientX, y: event.clientY });
    
    if (nodeType === 'plugin') {
      setSelectedPluginNode({ position });
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
    if (selectedPluginNode) {
      const newNode = {
        id: getId(),
        type: 'plugin',
        position: selectedPluginNode.position,
        data: { 
          plugin: plugin,
          pluginId: plugin.plugin_id,
          label: plugin.name,
          config: {},
          inputs: {},
          outputs: {}
        },
      };
      setNodes((nds) => nds.concat(newNode));
      setSelectedPluginNode(null);
    }
  }, [selectedPluginNode, setNodes]);

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
      <div className="sidebar">
        <h3>Node Library</h3>
        <div 
          className="node-item input-node" 
          onDragStart={(event) => onDragStart(event, 'input')}
          draggable
        >
          📥 Input Node
        </div>
        <div 
          className="node-item action-node" 
          onDragStart={(event) => onDragStart(event, 'default')}
          draggable
        >
          ⚡ Action Node
        </div>
        <div 
          className="node-item plugin-node" 
          onDragStart={(event) => onDragStart(event, 'plugin')}
          draggable
        >
          🔌 Plugin Node
        </div>
        <div 
          className="node-item http-node" 
          onDragStart={(event) => onDragStart(event, 'http')}
          draggable
        >
          🌐 HTTP Request
        </div>
        <div 
          className="node-item file-node" 
          onDragStart={(event) => onDragStart(event, 'file')}
          draggable
        >
          📁 File Operation
        </div>
        <div 
          className="node-item database-node" 
          onDragStart={(event) => onDragStart(event, 'database')}
          draggable
        >
          🗄️ Database
        </div>
        <div 
          className="node-item condition-node" 
          onDragStart={(event) => onDragStart(event, 'condition')}
          draggable
        >
          🔀 Condition
        </div>
        <div 
          className="node-item delay-node" 
          onDragStart={(event) => onDragStart(event, 'delay')}
          draggable
        >
          ⏱️ Delay
        </div>
        <div 
          className="node-item output-node" 
          onDragStart={(event) => onDragStart(event, 'output')}
          draggable
        >
          📤 Output
        </div>
      </div>
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
      <PluginSelector
        isOpen={showPluginSelector}
        onClose={() => setShowPluginSelector(false)}
        onPluginSelect={handlePluginSelect}
      />
    </div>
  );
}

function FlowCanvas(props) {
  return (
    <ReactFlowProvider>
      <FlowCanvasContent {...props} />
    </ReactFlowProvider>
  );
}

export default FlowCanvas;