import React, { useState, useEffect } from 'react';
import { Handle, Position } from '@xyflow/react';
import PluginAPI from '../PluginAPI';
import './PluginNode.css';

const PluginNode = ({ id, data, isConnectable }) => {
  const [pluginDetails, setPluginDetails] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [inputValues, setInputValues] = useState({});
  const [lastResult, setLastResult] = useState(null);

  useEffect(() => {
    if (data.pluginId) {
      loadPluginDetails();
    }
  }, [data.pluginId]);

  const loadPluginDetails = async () => {
    setLoading(true);
    setError(null);
    try {
      const details = await PluginAPI.getPluginDetails(data.pluginId);
      setPluginDetails(details);
      
      // Initialize input values with defaults
      if (details.input_schema?.properties) {
        const defaults = {};
        Object.entries(details.input_schema.properties).forEach(([key, prop]) => {
          if (prop.default !== undefined) {
            defaults[key] = prop.default;
          }
        });
        setInputValues(prev => ({ ...defaults, ...prev }));
      }
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  const handleInputChange = (key, value) => {
    setInputValues(prev => ({
      ...prev,
      [key]: value
    }));
  };

  const handleExecute = async () => {
    setError(null);
    setLoading(true);
    try {
      const result = await PluginAPI.executePlugin(data.pluginId, inputValues);
      setLastResult(result);
      
      // Update node data with result
      if (data.onDataChange) {
        data.onDataChange(id, { ...data, lastResult: result });
      }
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  if (loading && !pluginDetails) {
    return (
      <div className="plugin-node loading">
        <div className="plugin-header">
          <div className="plugin-icon">🔌</div>
          <div className="plugin-title">Loading Plugin...</div>
        </div>
        <div className="plugin-content">
          <div className="loading-spinner"></div>
        </div>
        <Handle
          type="target"
          position={Position.Left}
          isConnectable={isConnectable}
        />
        <Handle
          type="source"
          position={Position.Right}
          isConnectable={isConnectable}
        />
      </div>
    );
  }

  if (error) {
    return (
      <div className="plugin-node error">
        <div className="plugin-header">
          <div className="plugin-icon">❌</div>
          <div className="plugin-title">Plugin Error</div>
        </div>
        <div className="plugin-content">
          <div className="error-message">{error}</div>
          <button onClick={loadPluginDetails} className="retry-button">
            Retry
          </button>
        </div>
        <Handle
          type="target"
          position={Position.Left}
          isConnectable={isConnectable}
        />
        <Handle
          type="source"
          position={Position.Right}
          isConnectable={isConnectable}
        />
      </div>
    );
  }

  if (!data.pluginId) {
    return (
      <div className="plugin-node">
        <div className="plugin-header">
          <div className="plugin-icon">🔌</div>
          <div className="plugin-title">Plugin Node</div>
        </div>
        <div className="plugin-content">
          <div className="plugin-selector">
            <button 
              onClick={() => {
                if (data.onPluginSelect) {
                  data.onPluginSelect(id);
                }
              }}
              className="select-plugin-button"
            >
              Select Plugin
            </button>
          </div>
        </div>
        <Handle
          type="target"
          position={Position.Left}
          isConnectable={isConnectable}
        />
        <Handle
          type="source"
          position={Position.Right}
          isConnectable={isConnectable}
        />
      </div>
    );
  }

  return (
    <div className="plugin-node">
      <div className="plugin-header">
        <div className="plugin-icon">🔌</div>
        <div className="plugin-title">{pluginDetails?.name || data.pluginId}</div>
        <button
          className="change-plugin-button"
          onClick={() => {
            if (data.onPluginSelect) {
              data.onPluginSelect(id);
            }
          }}
          title="Change Plugin"
        >
          ⚙️
        </button>
      </div>
      
      <div className="plugin-content">
        {pluginDetails?.description && (
          <div className="plugin-description">{pluginDetails.description}</div>
        )}
        
        {pluginDetails?.input_schema?.properties && (
          <div className="plugin-inputs">
            <h4>Inputs:</h4>
            {Object.entries(pluginDetails.input_schema.properties).map(([key, prop]) => (
              <div key={key} className="input-field">
                <label htmlFor={`${id}-${key}`}>{prop.title || key}:</label>
                {prop.enum ? (
                  <select
                    id={`${id}-${key}`}
                    value={inputValues[key] || prop.default || ''}
                    onChange={(e) => handleInputChange(key, e.target.value)}
                    disabled={loading}
                  >
                    <option value="">Select...</option>
                    {prop.enum.map(option => (
                      <option key={option} value={option}>{option}</option>
                    ))}
                  </select>
                ) : prop.type === 'number' ? (
                  <input
                    type="number"
                    id={`${id}-${key}`}
                    value={inputValues[key] || prop.default || ''}
                    onChange={(e) => handleInputChange(key, parseFloat(e.target.value))}
                    disabled={loading}
                    min={prop.minimum}
                    max={prop.maximum}
                  />
                ) : prop.type === 'boolean' ? (
                  <input
                    type="checkbox"
                    id={`${id}-${key}`}
                    checked={inputValues[key] || prop.default || false}
                    onChange={(e) => handleInputChange(key, e.target.checked)}
                    disabled={loading}
                  />
                ) : (
                  <input
                    type="text"
                    id={`${id}-${key}`}
                    value={inputValues[key] || prop.default || ''}
                    onChange={(e) => handleInputChange(key, e.target.value)}
                    disabled={loading}
                    placeholder={prop.description || ''}
                  />
                )}
                {prop.description && (
                  <small className="field-description">{prop.description}</small>
                )}
              </div>
            ))}
          </div>
        )}
        
        <div className="plugin-actions">
          <button
            onClick={handleExecute}
            disabled={loading}
            className="execute-button"
          >
            {loading ? 'Executing...' : 'Execute'}
          </button>
        </div>
        
        {lastResult && (
          <div className="plugin-result">
            <h4>Last Result:</h4>
            <div className={`result-status ${lastResult.success ? 'success' : 'error'}`}>
              {lastResult.success ? '✅ Success' : '❌ Failed'}
            </div>
            {lastResult.error && (
              <div className="result-error">{lastResult.error}</div>
            )}
            {Object.entries(lastResult).filter(([key]) => key !== 'success' && key !== 'error').map(([key, value]) => (
              <div key={key} className="result-field">
                <strong>{key}:</strong>
                <span className="result-value">
                  {typeof value === 'object' ? JSON.stringify(value, null, 2) : String(value)}
                </span>
              </div>
            ))}
          </div>
        )}
      </div>
      
      <Handle
        type="target"
        position={Position.Left}
        isConnectable={isConnectable}
      />
      <Handle
        type="source"
        position={Position.Right}
        isConnectable={isConnectable}
      />
    </div>
  );
};

export default PluginNode;