/**
 * Workflow JSON Schema and Utility Functions
 * 
 * Workflow Structure:
 * {
 *   id: string,
 *   name: string,
 *   description: string,
 *   nodes: Array<Node>,
 *   edges: Array<Edge>,
 *   created_at: string,
 *   updated_at: string
 * }
 * 
 * Node Structure:
 * {
 *   id: string,
 *   type: 'input' | 'action' | 'http_request' | 'file_read' | 'condition',
 *   position: { x: number, y: number },
 *   data: {
 *     label: string,
 *     config: { [key: string]: any }
 *   }
 * }
 * 
 * Edge Structure:
 * {
 *   id: string,
 *   source: string,
 *   target: string,
 *   sourceHandle?: string,
 *   targetHandle?: string
 * }
 */

/**
 * Convert React Flow nodes and edges to workflow JSON format
 */
export function exportWorkflow(nodes, edges, workflowName = 'Untitled Workflow', description = '') {
  const workflow = {
    id: generateWorkflowId(),
    name: workflowName,
    description: description,
    nodes: nodes.map(node => ({
      id: node.id,
      type: node.type || 'default',
      position: node.position,
      data: {
        label: node.data?.label || '',
        config: node.data?.config || {}
      }
    })),
    edges: edges.map(edge => ({
      id: edge.id,
      source: edge.source,
      target: edge.target,
      sourceHandle: edge.sourceHandle,
      targetHandle: edge.targetHandle
    })),
    created_at: new Date().toISOString(),
    updated_at: new Date().toISOString()
  };

  return workflow;
}

/**
 * Convert workflow JSON format to React Flow nodes and edges
 */
export function importWorkflow(workflow) {
  if (!workflow || !workflow.nodes || !workflow.edges) {
    throw new Error('Invalid workflow format');
  }

  const nodes = workflow.nodes.map(node => ({
    id: node.id,
    type: node.type,
    position: node.position,
    data: {
      label: node.data?.label || '',
      config: node.data?.config || {}
    }
  }));

  const edges = workflow.edges.map(edge => ({
    id: edge.id,
    source: edge.source,
    target: edge.target,
    sourceHandle: edge.sourceHandle,
    targetHandle: edge.targetHandle
  }));

  return { nodes, edges };
}

/**
 * Download workflow as JSON file
 */
export function downloadWorkflow(workflow) {
  const dataStr = JSON.stringify(workflow, null, 2);
  const dataBlob = new Blob([dataStr], { type: 'application/json' });
  const url = URL.createObjectURL(dataBlob);
  
  const link = document.createElement('a');
  link.href = url;
  link.download = `${workflow.name.replace(/\s+/g, '_')}.json`;
  document.body.appendChild(link);
  link.click();
  document.body.removeChild(link);
  
  URL.revokeObjectURL(url);
}

/**
 * Load workflow from file upload
 */
export function loadWorkflowFromFile(file) {
  return new Promise((resolve, reject) => {
    const reader = new FileReader();
    
    reader.onload = (event) => {
      try {
        const workflow = JSON.parse(event.target.result);
        const { nodes, edges } = importWorkflow(workflow);
        resolve({ workflow, nodes, edges });
      } catch (error) {
        reject(new Error('Failed to parse workflow file: ' + error.message));
      }
    };
    
    reader.onerror = () => {
      reject(new Error('Failed to read file'));
    };
    
    reader.readAsText(file);
  });
}

/**
 * Generate unique workflow ID
 */
function generateWorkflowId() {
  return 'workflow_' + Date.now() + '_' + Math.random().toString(36).substr(2, 9);
}

/**
 * Validate workflow structure
 */
export function validateWorkflow(workflow) {
  if (!workflow || typeof workflow !== 'object') {
    return { valid: false, error: 'Workflow must be an object' };
  }

  if (!workflow.nodes || !Array.isArray(workflow.nodes)) {
    return { valid: false, error: 'Workflow must have a nodes array' };
  }

  if (!workflow.edges || !Array.isArray(workflow.edges)) {
    return { valid: false, error: 'Workflow must have an edges array' };
  }

  // Validate nodes
  for (const node of workflow.nodes) {
    if (!node.id || !node.type || !node.position) {
      return { valid: false, error: 'Each node must have id, type, and position' };
    }
    if (typeof node.position.x !== 'number' || typeof node.position.y !== 'number') {
      return { valid: false, error: 'Node position must have numeric x and y coordinates' };
    }
  }

  // Validate edges
  for (const edge of workflow.edges) {
    if (!edge.id || !edge.source || !edge.target) {
      return { valid: false, error: 'Each edge must have id, source, and target' };
    }
  }

  return { valid: true };
}