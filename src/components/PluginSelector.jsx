import React, { useState, useEffect } from 'react';
import PluginAPI from '../PluginAPI';
import './PluginSelector.css';

const PluginSelector = ({ isOpen, onClose, onPluginSelect }) => {
  const [plugins, setPlugins] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [selectedCategory, setSelectedCategory] = useState('all');

  useEffect(() => {
    if (isOpen) {
      loadPlugins();
    }
  }, [isOpen]);

  const loadPlugins = async () => {
    setLoading(true);
    setError(null);
    try {
      const pluginList = await PluginAPI.listPlugins();
      setPlugins(pluginList);
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  const categories = ['all', ...new Set(plugins.map(p => p.category || 'general'))];

  const filteredPlugins = selectedCategory === 'all' 
    ? plugins 
    : plugins.filter(p => (p.category || 'general') === selectedCategory);

  if (!isOpen) return null;

  return (
    <div className="plugin-selector-overlay" onClick={onClose}>
      <div className="plugin-selector-modal" onClick={(e) => e.stopPropagation()}>
        <div className="plugin-selector-header">
          <h2>Select Plugin</h2>
          <button className="close-button" onClick={onClose}>×</button>
        </div>
        
        <div className="plugin-selector-content">
          {loading && (
            <div className="loading-container">
              <div className="loading-spinner"></div>
              <p>Loading plugins...</p>
            </div>
          )}
          
          {error && (
            <div className="error-container">
              <div className="error-message">{error}</div>
              <button onClick={loadPlugins} className="retry-button">
                Retry
              </button>
            </div>
          )}
          
          {!loading && !error && (
            <>
              <div className="plugin-categories">
                {categories.map(category => (
                  <button
                    key={category}
                    className={`category-button ${selectedCategory === category ? 'active' : ''}`}
                    onClick={() => setSelectedCategory(category)}
                  >
                    {category.charAt(0).toUpperCase() + category.slice(1)}
                  </button>
                ))}
              </div>
              
              <div className="plugin-grid">
                {filteredPlugins.map(plugin => (
                  <div
                    key={plugin.plugin_id}
                    className="plugin-card"
                    onClick={() => {
                      onPluginSelect(plugin);
                      onClose();
                    }}
                  >
                    <div className="plugin-card-header">
                      <div className="plugin-icon">🔌</div>
                      <div className="plugin-info">
                        <h3>{plugin.name}</h3>
                        <span className="plugin-version">v{plugin.version}</span>
                      </div>
                    </div>
                    <div className="plugin-description">
                      {plugin.description}
                    </div>
                    <div className="plugin-footer">
                      <span className="plugin-author">by {plugin.author}</span>
                      <span className="plugin-category">{plugin.category || 'general'}</span>
                    </div>
                  </div>
                ))}
              </div>
              
              {filteredPlugins.length === 0 && (
                <div className="no-plugins">
                  <p>No plugins found in this category.</p>
                </div>
              )}
            </>
          )}
        </div>
      </div>
    </div>
  );
};

export default PluginSelector;