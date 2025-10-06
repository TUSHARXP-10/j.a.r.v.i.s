import React, { useState, useEffect } from 'react';
import { workflowAPI } from '../api';
import { useAuth } from '../contexts/AuthContext';
import './ExecutionLogs.css';

const ExecutionLogs = ({ workflowId, onClose }) => {
  const { hasAnyRole } = useAuth();
  const [logs, setLogs] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [filters, setFilters] = useState({
    status: '',
    startDate: '',
    endDate: '',
    scheduleId: ''
  });
  const [searchTerm, setSearchTerm] = useState('');
  const [statusStats, setStatusStats] = useState({});
  const [expandedLogs, setExpandedLogs] = useState(new Set());

  useEffect(() => {
    if (workflowId) {
      loadLogs();
    }
  }, [workflowId, filters]);

  const loadLogs = async () => {
    try {
      setLoading(true);
      setError(null);
      
      // Build query parameters
      const params = {};
      if (filters.status) params.status = filters.status;
      if (filters.startDate) params.start_date = filters.startDate;
      if (filters.endDate) params.end_date = filters.endDate;
      if (filters.scheduleId) params.schedule_id = filters.scheduleId;
      
      const logsData = await workflowAPI.getWorkflowExecutionLogs(workflowId, params);
      setLogs(logsData);
      
      // Calculate status statistics
      const stats = {};
      logsData.forEach(log => {
        stats[log.status] = (stats[log.status] || 0) + 1;
      });
      setStatusStats(stats);
    } catch (err) {
      setError('Failed to load execution logs');
      console.error('Error loading logs:', err);
    } finally {
      setLoading(false);
    }
  };

  const handleFilterChange = (field, value) => {
    setFilters(prev => ({ ...prev, [field]: value }));
  };

  const clearFilters = () => {
    setFilters({
      status: '',
      startDate: '',
      endDate: '',
      scheduleId: ''
    });
    setSearchTerm('');
  };

  const toggleLogExpansion = (logId) => {
    const newExpanded = new Set(expandedLogs);
    if (newExpanded.has(logId)) {
      newExpanded.delete(logId);
    } else {
      newExpanded.add(logId);
    }
    setExpandedLogs(newExpanded);
  };

  const exportLogs = () => {
    const dataStr = JSON.stringify(filteredLogs, null, 2);
    const dataBlob = new Blob([dataStr], { type: 'application/json' });
    const url = URL.createObjectURL(dataBlob);
    const link = document.createElement('a');
    link.href = url;
    link.download = `workflow-${workflowId}-logs-${new Date().toISOString()}.json`;
    link.click();
    URL.revokeObjectURL(url);
  };

  const copyLogDetails = (log) => {
    const details = {
      id: log.id,
      status: log.status,
      execution_time: log.execution_time,
      workflow_id: log.workflow_id,
      schedule_id: log.schedule_id,
      input_data: log.input_data,
      output_data: log.output_data,
      error_message: log.error_message
    };
    navigator.clipboard.writeText(JSON.stringify(details, null, 2));
  };

  const getStatusColor = (status) => {
    switch (status) {
      case 'success': return '#28a745';
      case 'error': return '#dc3545';
      case 'running': return '#ffc107';
      default: return '#6c757d';
    }
  };

  // Filter logs based on search term
  const filteredLogs = logs.filter(log => {
    if (!searchTerm) return true;
    
    const searchLower = searchTerm.toLowerCase();
    return (
      log.status.toLowerCase().includes(searchLower) ||
      (log.error_message && log.error_message.toLowerCase().includes(searchLower)) ||
      (log.input_data && JSON.stringify(log.input_data).toLowerCase().includes(searchLower)) ||
      (log.output_data && JSON.stringify(log.output_data).toLowerCase().includes(searchLower)) ||
      (log.schedule_id && log.schedule_id.toString().includes(searchTerm))
    );
  });

  const formatDate = (dateString) => {
    return new Date(dateString).toLocaleString();
  };

  const formatJson = (data) => {
    try {
      return JSON.stringify(data, null, 2);
    } catch {
      return String(data);
    }
  };

  return (
    <div className="execution-logs-modal">
      <div className="execution-logs-header">
        <h2>Execution Logs</h2>
        <button className="close-button" onClick={onClose}>×</button>
      </div>
      
      {/* Status Statistics */}
      <div className="execution-logs-stats">
        <h3>Execution Summary</h3>
        <div className="stats-row">
          {Object.entries(statusStats).map(([status, count]) => (
            <div key={status} className="stat-item" style={{ backgroundColor: getStatusColor(status) }}>
              <span className="stat-count">{count}</span>
              <span className="stat-label">{status}</span>
            </div>
          ))}
          <div className="stat-item total">
            <span className="stat-count">{logs.length}</span>
            <span className="stat-label">Total</span>
          </div>
        </div>
      </div>

      {/* Search and Action Bar */}
      <div className="execution-logs-toolbar">
        <div className="search-group">
          <input
            type="text"
            placeholder="Search logs (status, error, data, schedule ID)..."
            value={searchTerm}
            onChange={(e) => setSearchTerm(e.target.value)}
            className="search-input"
          />
          <span className="search-results">{filteredLogs.length} of {logs.length} logs</span>
        </div>
        
        <div className="action-buttons">
          {hasAnyRole(['admin', 'creator']) && (
            <button onClick={exportLogs} className="export-btn" disabled={filteredLogs.length === 0}>
              Export Logs
            </button>
          )}
          <button onClick={clearFilters} className="clear-filters-btn">
            Clear All
          </button>
        </div>
      </div>

      <div className="execution-logs-filters">
        <div className="filter-row">
          <div className="filter-group">
            <label>Status:</label>
            <select 
              value={filters.status} 
              onChange={(e) => handleFilterChange('status', e.target.value)}
            >
              <option value="">All</option>
              <option value="success">Success</option>
              <option value="error">Error</option>
              <option value="running">Running</option>
            </select>
          </div>
          
          <div className="filter-group">
            <label>Start Date:</label>
            <input 
              type="datetime-local" 
              value={filters.startDate}
              onChange={(e) => handleFilterChange('startDate', e.target.value)}
            />
          </div>
          
          <div className="filter-group">
            <label>End Date:</label>
            <input 
              type="datetime-local" 
              value={filters.endDate}
              onChange={(e) => handleFilterChange('endDate', e.target.value)}
            />
          </div>
          
          <div className="filter-group">
            <label>Schedule ID:</label>
            <input 
              type="number" 
              value={filters.scheduleId}
              onChange={(e) => handleFilterChange('scheduleId', e.target.value)}
              placeholder="Optional"
            />
          </div>
        </div>
      </div>
      
      <div className="execution-logs-content">
        {loading ? (
          <div className="loading">Loading logs...</div>
        ) : error ? (
          <div className="error">{error}</div>
        ) : filteredLogs.length === 0 ? (
          <div className="no-logs">
            {searchTerm ? `No logs match "${searchTerm}"` : 'No execution logs found'}
          </div>
        ) : (
          <div className="logs-list">
            {filteredLogs.map((log) => {
              const isExpanded = expandedLogs.has(log.id);
              return (
                <div key={log.id} className={`log-item ${isExpanded ? 'expanded' : ''}`}>
                  <div className="log-header">
                    <span 
                      className="log-status" 
                      style={{ backgroundColor: getStatusColor(log.status) }}
                    >
                      {log.status}
                    </span>
                    <span className="log-date">
                      {formatDate(log.execution_time)}
                    </span>
                    {log.schedule_id && (
                      <span className="log-schedule">
                        Schedule #{log.schedule_id}
                      </span>
                    )}
                    <div className="log-actions">
                      <button 
                        className="expand-btn"
                        onClick={() => toggleLogExpansion(log.id)}
                        title={isExpanded ? 'Collapse details' : 'Expand details'}
                      >
                        {isExpanded ? '−' : '+'}
                      </button>
                      {hasAnyRole(['admin', 'creator']) && (
                        <button 
                          className="copy-btn"
                          onClick={() => copyLogDetails(log)}
                          title="Copy log details"
                        >
                          📋
                        </button>
                      )}
                    </div>
                  </div>
                  
                  {isExpanded && (
                    <div className="log-details">
                      {log.input_data && (
                        <div className="log-section">
                          <h4>Input Data:</h4>
                          <pre className="log-data">{formatJson(log.input_data)}</pre>
                        </div>
                      )}
                      
                      {log.output_data && (
                        <div className="log-section">
                          <h4>Output Data:</h4>
                          <pre className="log-data">{formatJson(log.output_data)}</pre>
                        </div>
                      )}
                      
                      {log.error_message && (
                        <div className="log-section">
                          <h4>Error:</h4>
                          <pre className="log-error">{log.error_message}</pre>
                        </div>
                      )}
                      
                      <div className="log-metadata">
                        <strong>Log ID:</strong> {log.id} | 
                        <strong>Workflow ID:</strong> {log.workflow_id}
                        {log.schedule_id && ` | Schedule ID: ${log.schedule_id}`}
                      </div>
                    </div>
                  )}
                </div>
              );
            })}
          </div>
        )}
      </div>
    </div>
  );
};

export default ExecutionLogs;