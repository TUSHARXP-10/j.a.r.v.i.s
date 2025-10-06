import React from 'react';
import * as RF from '@xyflow/react';
const { Handle, Position } = RF;

export function InputNode({ data }) {
  return (
    <div className="react-flow__node-input">
      <Handle type="source" position={Position.Right} />
      <div>
        <strong>Input Node</strong>
        {data.label && <div>{data.label}</div>}
      </div>
    </div>
  );
}

export function ActionNode({ data }) {
  return (
    <div className="react-flow__node-default">
      <Handle type="target" position={Position.Left} />
      <div>
        <strong>Action Node</strong>
        {data.label && <div>{data.label}</div>}
      </div>
      <Handle type="source" position={Position.Right} />
    </div>
  );
}

export function HttpNode({ data }) {
  return (
    <div className="react-flow__node-http">
      <Handle type="target" position={Position.Left} />
      <div>
        <strong>HTTP Request</strong>
        {data.label && <div>{data.label}</div>}
      </div>
      <Handle type="source" position={Position.Right} />
    </div>
  );
}

export function FileNode({ data }) {
  return (
    <div className="react-flow__node-file">
      <Handle type="target" position={Position.Left} />
      <div>
        <strong>File Operation</strong>
        {data.label && <div>{data.label}</div>}
      </div>
      <Handle type="source" position={Position.Right} />
    </div>
  );
}

export function DatabaseNode({ data }) {
  return (
    <div className="react-flow__node-database">
      <Handle type="target" position={Position.Left} />
      <div>
        <strong>Database</strong>
        {data.label && <div>{data.label}</div>}
      </div>
      <Handle type="source" position={Position.Right} />
    </div>
  );
}

export function ConditionNode({ data }) {
  return (
    <div className="react-flow__node-condition">
      <Handle type="target" position={Position.Left} />
      <div>
        <strong>Condition</strong>
        {data.label && <div>{data.label}</div>}
      </div>
      <Handle type="source" position={Position.Right} id="true" />
      <Handle type="source" position={Position.Bottom} id="false" />
    </div>
  );
}

export function DelayNode({ data }) {
  return (
    <div className="react-flow__node-delay">
      <Handle type="target" position={Position.Left} />
      <div>
        <strong>Delay</strong>
        {data.label && <div>{data.label}</div>}
      </div>
      <Handle type="source" position={Position.Right} />
    </div>
  );
}

export function OutputNode({ data }) {
  return (
    <div className="react-flow__node-output">
      <Handle type="target" position={Position.Left} />
      <div>
        <strong>Output</strong>
        {data.label && <div>{data.label}</div>}
      </div>
    </div>
  );
}