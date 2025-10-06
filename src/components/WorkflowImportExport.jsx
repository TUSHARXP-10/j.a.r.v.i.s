import React, { useState, useRef } from 'react';
import { saveAs } from 'file-saver';
import './WorkflowImportExport.css';

const WorkflowImportExport = ({ workflow, onImportSuccess, workflows = [] }) => {
  const [isImporting, setIsImporting] = useState(false);
  const [importError, setImportError] = useState('');
  const [isExporting, setIsExporting] = useState(false);
  const [selectedWorkflows, setSelectedWorkflows] = useState([]);
  const [showBulkExport, setShowBulkExport] = useState(false);
  const fileInputRef = useRef(null);

  // Export single workflow
  const exportWorkflow = async (format = 'json') => {
    if (!workflow?.id) return;
    
    setIsExporting(true);
    try {
      const response = await fetch(`/workflows/${workflow.id}/export?format=${format}`, {
        headers: {
          'Authorization': `Bearer ${localStorage.getItem('token')}`
        }
      });

      if (!response.ok) {
        throw new Error(`Export failed: ${response.statusText}`);
      }

      const blob = await response.blob();
      const contentDisposition = response.headers.get('Content-Disposition');
      const filename = contentDisposition 
        ? contentDisposition.split('filename=')[1].replace(/['"]/g, '')
        : `workflow_${workflow.name.replace(/\s+/g, '_')}_${workflow.id}.${format}`;

      saveAs(blob, filename);
    } catch (error) {
      console.error('Export error:', error);
      alert('Export failed: ' + error.message);
    } finally {
      setIsExporting(false);
    }
  };

  // Import workflow
  const importWorkflow = async (file) => {
    if (!file) return;

    setIsImporting(true);
    setImportError('');

    const formData = new FormData();
    formData.append('file', file);

    try {
      const response = await fetch('/workflows/import', {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${localStorage.getItem('token')}`
        },
        body: formData
      });

      if (!response.ok) {
        const errorData = await response.json().catch(() => ({ detail: 'Import failed' }));
        throw new Error(errorData.detail || 'Import failed');
      }

      const importedWorkflow = await response.json();
      
      if (onImportSuccess) {
        onImportSuccess(importedWorkflow);
      }
      
      // Clear file input
      if (fileInputRef.current) {
        fileInputRef.current.value = '';
      }
      
      alert('Workflow imported successfully!');
    } catch (error) {
      console.error('Import error:', error);
      setImportError(error.message);
    } finally {
      setIsImporting(false);
    }
  };

  // Handle file selection
  const handleFileSelect = (event) => {
    const file = event.target.files[0];
    if (file) {
      importWorkflow(file);
    }
  };

  // Bulk export workflows
  const exportSelectedWorkflows = async () => {
    if (selectedWorkflows.length === 0) {
      alert('Please select at least one workflow to export');
      return;
    }

    setIsExporting(true);
    try {
      const response = await fetch('/workflows/bulk-export', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${localStorage.getItem('token')}`
        },
        body: JSON.stringify({ workflow_ids: selectedWorkflows })
      });

      if (!response.ok) {
        throw new Error(`Bulk export failed: ${response.statusText}`);
      }

      const blob = await response.blob();
      const contentDisposition = response.headers.get('Content-Disposition');
      const filename = contentDisposition 
        ? contentDisposition.split('filename=')[1].replace(/['"]/g, '')
        : `workflows_bulk_export_${new Date().toISOString().split('T')[0]}.zip`;

      saveAs(blob, filename);
      setShowBulkExport(false);
      setSelectedWorkflows([]);
    } catch (error) {
      console.error('Bulk export error:', error);
      alert('Bulk export failed: ' + error.message);
    } finally {
      setIsExporting(false);
    }
  };

  // Toggle workflow selection for bulk export
  const toggleWorkflowSelection = (workflowId) => {
    setSelectedWorkflows(prev => 
      prev.includes(workflowId) 
        ? prev.filter(id => id !== workflowId)
        : [...prev, workflowId]
    );
  };

  // Single workflow view
  if (workflow) {
    return (
      <div className="workflow-import-export">
        <h3>Export Workflow</h3>
        <div className="export-options">
          <button 
            onClick={() => exportWorkflow('json')}
            disabled={isExporting}
            className="export-btn json-btn"
          >
            {isExporting ? 'Exporting...' : 'Export as JSON'}
          </button>
          <button 
            onClick={() => exportWorkflow('zip')}
            disabled={isExporting}
            className="export-btn zip-btn"
          >
            {isExporting ? 'Exporting...' : 'Export as ZIP'}
          </button>
        </div>
      </div>
    );
  }

  // Multiple workflows view (for workflow list)
  return (
    <div className="workflow-import-export">
      <div className="import-section">
        <h3>Import Workflow</h3>
        <input
          type="file"
          ref={fileInputRef}
          onChange={handleFileSelect}
          accept=".json,.zip"
          disabled={isImporting}
          className="file-input"
        />
        {isImporting && <div className="loading">Importing...</div>}
        {importError && <div className="error">{importError}</div>}
      </div>

      {workflows.length > 0 && (
        <div className="bulk-export-section">
          <h3>Bulk Export</h3>
          {!showBulkExport ? (
            <button 
              onClick={() => setShowBulkExport(true)}
              className="bulk-export-btn"
            >
              Select Workflows for Export
            </button>
          ) : (
            <div className="bulk-export-panel">
              <div className="workflow-selection">
                <h4>Select Workflows to Export:</h4>
                {workflows.map(wf => (
                  <label key={wf.id} className="workflow-checkbox">
                    <input
                      type="checkbox"
                      checked={selectedWorkflows.includes(wf.id)}
                      onChange={() => toggleWorkflowSelection(wf.id)}
                    />
                    <span>{wf.name}</span>
                    {wf.description && <small> - {wf.description}</small>}
                  </label>
                ))}
              </div>
              <div className="bulk-export-actions">
                <button 
                  onClick={exportSelectedWorkflows}
                  disabled={isExporting || selectedWorkflows.length === 0}
                  className="export-selected-btn"
                >
                  {isExporting ? 'Exporting...' : `Export Selected (${selectedWorkflows.length})`}
                </button>
                <button 
                  onClick={() => {
                    setShowBulkExport(false);
                    setSelectedWorkflows([]);
                  }}
                  className="cancel-btn"
                >
                  Cancel
                </button>
              </div>
            </div>
          )}
        </div>
      )}
    </div>
  );
};

export default WorkflowImportExport;