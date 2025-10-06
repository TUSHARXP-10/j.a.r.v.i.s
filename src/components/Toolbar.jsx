import React, { useRef, useState } from 'react';
import { useAuth } from '../contexts/AuthContext';
import ScheduleModal from './ScheduleModal';
import './Toolbar.css';

function Toolbar({ 
  onExport, 
  onImport, 
  workflowName, 
  setWorkflowName, 
  onSave, 
  onExecute, 
  isLoading,
  savedWorkflows = [], 
  onLoadWorkflow, 
  workflowRuns = [], 
  schedules = [], 
  createSchedule, 
  updateSchedule, 
  deleteSchedule, 
  toggleSchedule, 
  onShowExecutionLogs, 
  onShowSharing 
}) {
  const { hasRole, hasAnyRole } = useAuth();
  const fileInputRef = useRef(null);
  const [showScheduleModal, setShowScheduleModal] = useState(false);
  const [editingSchedule, setEditingSchedule] = useState(null);

  const handleImportClick = () => {
    fileInputRef.current?.click();
  };

  const handleFileChange = (event) => {
    const file = event.target.files[0];
    if (file) {
      const reader = new FileReader();
      reader.onload = (e) => {
        try {
          const workflow = JSON.parse(e.target.result);
          onImport(workflow.nodes, workflow.edges);
        } catch (error) {
          alert('Error importing workflow: ' + error.message);
        }
      };
      reader.readAsText(file);
    }
    event.target.value = '';
  };

  const handleCreateSchedule = () => {
    setEditingSchedule(null);
    setShowScheduleModal(true);
  };

  const handleEditSchedule = (schedule) => {
    setEditingSchedule(schedule);
    setShowScheduleModal(true);
  };

  const handleSaveSchedule = (scheduleData) => {
    if (editingSchedule) {
      updateSchedule(editingSchedule.id, scheduleData);
    } else {
      createSchedule(scheduleData);
    }
    setShowScheduleModal(false);
    setEditingSchedule(null);
  };

  return (
    <div className="toolbar">
      <input
        type="text"
        placeholder="Workflow Name"
        value={workflowName}
        onChange={(e) => setWorkflowName(e.target.value)}
        className="workflow-name-input"
      />
      {hasAnyRole(['admin', 'creator']) && (
        <button onClick={onSave} disabled={isLoading} className="toolbar-button">
          {isLoading ? 'Saving...' : 'Save'}
        </button>
      )}
      {hasAnyRole(['admin', 'creator']) && (
        <button onClick={onExecute} disabled={isLoading} className="toolbar-button">
          {isLoading ? 'Executing...' : 'Execute'}
        </button>
      )}
      <button onClick={onExport} className="toolbar-button">
        Export JSON
      </button>
      <button onClick={handleImportClick} className="toolbar-button">
        Import JSON
      </button>
      <button onClick={onShowExecutionLogs} className="toolbar-button">
        Execution Logs
      </button>
      <button onClick={onShowSharing} className="toolbar-button">
        Share Workflow
      </button>
      
      {/* Workflow Load Dropdown */}
      <select 
        onChange={(e) => {
          if (e.target.value) {
            onLoadWorkflow(parseInt(e.target.value))
            e.target.value = ''
          }
        }} 
        className="toolbar-select"
        disabled={isLoading}
      >
        <option value="">Load Workflow...</option>
        {savedWorkflows.map(workflow => (
          <option key={workflow.id} value={workflow.id}>
            {workflow.name}
          </option>
        ))}
      </select>
      
      <input
        ref={fileInputRef}
        type="file"
        accept=".json"
        onChange={handleFileChange}
        style={{ display: 'none' }}
      />
      
      {workflowRuns.length > 0 && (
        <div className="toolbar-section">
          <h3>Execution History</h3>
          <div className="workflow-runs">
            {workflowRuns.map((run) => (
              <div key={run.id} className={`workflow-run ${run.status}`}>
                <div className="run-header">
                  <span className="run-status">{run.status}</span>
                  <span className="run-date">
                    {new Date(run.created_at).toLocaleString()}
                  </span>
                </div>
                {run.result && (
                  <div className="run-result">
                    {run.result.error ? (
                      <span className="error-text">Error: {run.result.error}</span>
                    ) : (
                      <span className="success-text">Success</span>
                    )}
                  </div>
                )}
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Scheduling Section */}
      {hasAnyRole(['admin', 'creator']) && (
        <div className="toolbar-section">
          <div className="section-header">
            <h3>Scheduling</h3>
            <button onClick={handleCreateSchedule} className="toolbar-button small">
              + New Schedule
            </button>
          </div>
          <div className="workflow-schedules">
            {schedules.map((schedule) => (
              <div key={schedule.id} className={`schedule-item ${schedule.enabled ? 'active' : 'inactive'}`}>
                <div className="schedule-header">
                  <span className="schedule-name">{schedule.name}</span>
                  <div className="schedule-actions">
                    <button
                      onClick={() => toggleSchedule(schedule.id)}
                      className={`toggle-button ${schedule.enabled ? 'enabled' : 'disabled'}`}
                      title={schedule.enabled ? 'Disable schedule' : 'Enable schedule'}
                    >
                      {schedule.enabled ? '⏸️' : '▶️'}
                    </button>
                    <button
                      onClick={() => handleEditSchedule(schedule)}
                      className="edit-button"
                      title="Edit schedule"
                    >
                      ✏️
                    </button>
                    <button
                      onClick={() => deleteSchedule(schedule.id)}
                      className="delete-button"
                      title="Delete schedule"
                    >
                      🗑️
                    </button>
                  </div>
                </div>
                <div className="schedule-details">
                  <div className="schedule-cron">{schedule.cron_expression}</div>
                  <div className="schedule-status">
                    {schedule.enabled ? 'Enabled' : 'Disabled'}
                  </div>
                </div>
              </div>
            ))}
          </div>
        </div>
      )}

      {showScheduleModal && (
        <ScheduleModal
          isOpen={showScheduleModal}
          onClose={() => setShowScheduleModal(false)}
          onSave={handleSaveSchedule}
          schedule={editingSchedule}
        />
      )}
    </div>
  );
}

export default Toolbar;