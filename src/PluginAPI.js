import axios from 'axios';

const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000';

const api = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
});

// Add auth token to requests
api.interceptors.request.use((config) => {
  const token = localStorage.getItem('token');
  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});

api.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error.response?.status === 401) {
      localStorage.removeItem('token');
      window.location.href = '/login';
    }
    return Promise.reject(error);
  }
);

export class PluginAPI {
  /**
   * List all available plugins
   * @returns {Promise<Array>} List of plugins
   */
  static async listPlugins() {
    try {
      const response = await api.get('/plugins');
      return response.data.plugins;
    } catch (error) {
      console.error('Error listing plugins:', error);
      throw error;
    }
  }

  /**
   * Get detailed information about a specific plugin
   * @param {string} pluginId - Plugin ID
   * @returns {Promise<Object>} Plugin details
   */
  static async getPluginDetails(pluginId) {
    try {
      const response = await api.get(`/plugins/${pluginId}`);
      return response.data;
    } catch (error) {
      console.error(`Error getting plugin details for ${pluginId}:`, error);
      throw error;
    }
  }

  /**
   * Execute a plugin with input data
   * @param {string} pluginId - Plugin ID
   * @param {Object} inputData - Input data for the plugin
   * @returns {Promise<Object>} Plugin execution result
   */
  static async executePlugin(pluginId, inputData) {
    try {
      const response = await api.post(`/plugins/${pluginId}/execute`, inputData);
      return response.data;
    } catch (error) {
      console.error(`Error executing plugin ${pluginId}:`, error);
      throw error;
    }
  }

  /**
   * Update plugin configuration (admin only)
   * @param {string} pluginId - Plugin ID
   * @param {Object} config - Configuration data
   * @returns {Promise<Object>} Update result
   */
  static async updatePluginConfig(pluginId, config) {
    try {
      const response = await api.post(`/plugins/${pluginId}/config`, config);
      return response.data;
    } catch (error) {
      console.error(`Error updating plugin config for ${pluginId}:`, error);
      throw error;
    }
  }

  /**
   * Get plugin configuration (admin only)
   * @param {string} pluginId - Plugin ID
   * @returns {Promise<Object>} Plugin configuration
   */
  static async getPluginConfig(pluginId) {
    try {
      const response = await api.get(`/plugins/${pluginId}/config`);
      return response.data;
    } catch (error) {
      console.error(`Error getting plugin config for ${pluginId}:`, error);
      throw error;
    }
  }
}

export default PluginAPI;