import axios from 'axios';

const API_BASE_URL = 'http://localhost:8000';

// Create axios instance with default config
const api = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
});

// Add auth token to requests
api.interceptors.request.use((config) => {
  const token = localStorage.getItem('access_token');
  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});

export const WorkflowAPI = {
  // Export single workflow
  exportWorkflow: async (workflowId, format = 'json') => {
    try {
      const response = await api.get(`/workflows/${workflowId}/export`, {
        params: { format },
        responseType: 'blob', // Important for file downloads
      });
      return response.data;
    } catch (error) {
      console.error('Export workflow error:', error);
      throw error;
    }
  },

  // Import workflow
  importWorkflow: async (file, overwrite = false) => {
    try {
      const formData = new FormData();
      formData.append('file', file);
      formData.append('overwrite', overwrite.toString());

      const response = await api.post('/workflows/import', formData, {
        headers: {
          'Content-Type': 'multipart/form-data',
        },
      });
      return response.data;
    } catch (error) {
      console.error('Import workflow error:', error);
      throw error;
    }
  },

  // Bulk export workflows
  bulkExportWorkflows: async (workflowIds, format = 'json') => {
    try {
      const response = await api.post('/workflows/bulk-export', {
        workflow_ids: workflowIds,
        format,
      }, {
        responseType: 'blob', // Important for file downloads
      });
      return response.data;
    } catch (error) {
      console.error('Bulk export workflows error:', error);
      throw error;
    }
  },

  // Get all workflows for selection (used in bulk export)
  getAllWorkflows: async () => {
    try {
      const response = await api.get('/workflows');
      return response.data;
    } catch (error) {
      console.error('Get workflows error:', error);
      throw error;
    }
  },

  // Download file helper
  downloadFile: (blob, filename) => {
    const url = window.URL.createObjectURL(blob);
    const link = document.createElement('a');
    link.href = url;
    link.download = filename;
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
    window.URL.revokeObjectURL(url);
  },

  // Generate filename based on workflow name and format
  generateFilename: (workflowName, format) => {
    const timestamp = new Date().toISOString().replace(/[:.]/g, '-');
    const sanitizedName = workflowName.replace(/[^a-zA-Z0-9-_]/g, '_');
    return `${sanitizedName}_${timestamp}.${format}`;
  },
};

export default WorkflowAPI;