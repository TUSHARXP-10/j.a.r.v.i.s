import React, { useState, useEffect } from 'react';
import { workflowAPI } from '../api';
import { useAuth } from '../contexts/AuthContext';
import './WorkflowSharing.css';

const WorkflowSharing = ({ workflowId, workflowName, onClose }) => {
  const { user } = useAuth();
  const [collaborators, setCollaborators] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [success, setSuccess] = useState(null);
  const [shareForm, setShareForm] = useState({
    user_email: '',
    permission_level: 'view'
  });
  const [updatingCollaborators, setUpdatingCollaborators] = useState(new Set());

  useEffect(() => {
    if (workflowId) {
      loadCollaborators();
    }
  }, [workflowId]);

  const loadCollaborators = async () => {
    try {
      setLoading(true);
      setError(null);
      const shares = await workflowAPI.getWorkflowShares(workflowId);
      setCollaborators(shares);
    } catch (err) {
      setError('Failed to load collaborators');
      console.error('Error loading collaborators:', err);
    } finally {
      setLoading(false);
    }
  };

  const handleShareWorkflow = async (e) => {
    e.preventDefault();
    try {
      setError(null);
      setSuccess(null);
      
      if (!shareForm.user_email.trim()) {
        setError('Please enter an email address');
        return;
      }

      await workflowAPI.shareWorkflow(workflowId, {
        user_email: shareForm.user_email.trim(),
        permission_level: shareForm.permission_level
      });

      setSuccess(`Workflow shared with ${shareForm.user_email}`);
      setShareForm({ user_email: '', permission_level: 'view' });
      await loadCollaborators();
    } catch (err) {
      setError(err.message || 'Failed to share workflow');
      console.error('Error sharing workflow:', err);
    }
  };

  const handleUpdatePermission = async (userId, newPermission) => {
    try {
      setUpdatingCollaborators(prev => new Set([...prev, userId]));
      setError(null);
      
      await workflowAPI.updateWorkflowShare(workflowId, userId, {
        permission_level: newPermission
      });
      
      await loadCollaborators();
    } catch (err) {
      setError('Failed to update permission');
      console.error('Error updating permission:', err);
    } finally {
      setUpdatingCollaborators(prev => {
        const newSet = new Set(prev);
        newSet.delete(userId);
        return newSet;
      });
    }
  };

  const handleRemoveCollaborator = async (userId, collaboratorName) => {
    if (!window.confirm(`Are you sure you want to remove ${collaboratorName} from this workflow?`)) {
      return;
    }

    try {
      setUpdatingCollaborators(prev => new Set([...prev, userId]));
      setError(null);
      
      await workflowAPI.deleteWorkflowShare(workflowId, userId);
      
      await loadCollaborators();
      setSuccess('Collaborator removed successfully');
    } catch (err) {
      setError('Failed to remove collaborator');
      console.error('Error removing collaborator:', err);
    } finally {
      setUpdatingCollaborators(prev => {
        const newSet = new Set(prev);
        newSet.delete(userId);
        return newSet;
      });
    }
  };

  const formatDate = (dateString) => {
    return new Date(dateString).toLocaleDateString('en-US', {
      year: 'numeric',
      month: 'short',
      day: 'numeric',
      hour: '2-digit',
      minute: '2-digit'
    });
  };

  if (!workflowId) {
    return null;
  }

  return (
    <div className="workflow-sharing">
      <div className="workflow-sharing-content">
        <div className="workflow-sharing-header">
          <h2>Share Workflow: {workflowName}</h2>
          <button className="close-button" onClick={onClose}>×</button>
        </div>

        {error && (
          <div className="error-message">
            {error}
          </div>
        )}

        {success && (
          <div className="success-message">
            {success}
          </div>
        )}

        <form className="share-form" onSubmit={handleShareWorkflow}>
          <h3>Share with someone</h3>
          <div className="form-group">
            <label htmlFor="user-email">Email Address:</label>
            <input
              id="user-email"
              type="email"
              placeholder="Enter email address"
              value={shareForm.user_email}
              onChange={(e) => setShareForm(prev => ({ ...prev, user_email: e.target.value }))}
              required
            />
          </div>
          <div className="form-group">
            <label htmlFor="permission-level">Permission Level:</label>
            <select
              id="permission-level"
              value={shareForm.permission_level}
              onChange={(e) => setShareForm(prev => ({ ...prev, permission_level: e.target.value }))}
            >
              <option value="view">View Only</option>
              <option value="edit">Can Edit</option>
            </select>
          </div>
          <div className="form-actions">
            <button type="submit" className="btn-primary" disabled={!shareForm.user_email.trim()}>
              Share Workflow
            </button>
          </div>
        </form>

        <div className="collaborators-list">
          <h3>Current Collaborators</h3>
          {loading ? (
            <div className="loading">Loading collaborators...</div>
          ) : collaborators.length === 0 ? (
            <div className="no-collaborators">
              No collaborators yet. Share this workflow with others to collaborate.
            </div>
          ) : (
            <div>
              {collaborators.map((collaborator) => (
                <div key={collaborator.user_id} className="collaborator-item">
                  <div className="collaborator-info">
                    <div className="collaborator-name">{collaborator.user.full_name || collaborator.user.email}</div>
                    <div className="collaborator-email">{collaborator.user.email}</div>
                    <div className="collaborator-date">Shared on {formatDate(collaborator.shared_at)}</div>
                  </div>
                  <div className="collaborator-permission">
                    <select
                      className="permission-select"
                      value={collaborator.permission_level}
                      onChange={(e) => handleUpdatePermission(collaborator.user_id, e.target.value)}
                      disabled={updatingCollaborators.has(collaborator.user_id)}
                    >
                      <option value="view">View Only</option>
                      <option value="edit">Can Edit</option>
                    </select>
                  </div>
                  <div className="collaborator-actions">
                    <button
                      className="btn-small btn-remove"
                      onClick={() => handleRemoveCollaborator(collaborator.user_id, collaborator.user.full_name || collaborator.user.email)}
                      disabled={updatingCollaborators.has(collaborator.user_id)}
                    >
                      Remove
                    </button>
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>
      </div>
    </div>
  );
};

export default WorkflowSharing;