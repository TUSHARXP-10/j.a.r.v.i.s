const API_BASE_URL = 'http://localhost:8000';

class WorkflowAPI {
  constructor() {
    this.baseUrl = API_BASE_URL;
  }

  async request(endpoint, options = {}) {
    const url = `${this.baseUrl}${endpoint}`;
    const config = {
      headers: {
        'Content-Type': 'application/json',
        ...options.headers,
      },
      ...options,
    };

    try {
      const response = await fetch(url, config);
      
      if (!response.ok) {
        const error = await response.json().catch(() => ({ detail: response.statusText }));
        throw new Error(error.detail || `HTTP ${response.status}`);
      }

      return await response.json();
    } catch (error) {
      console.error('API request failed:', error);
      throw error;
    }
  }

  // Workflow CRUD operations
  async createWorkflow(workflow) {
    return this.request('/workflows', {
      method: 'POST',
      body: JSON.stringify(workflow),
    });
  }

  async getWorkflows() {
    return this.request('/workflows');
  }

  async getWorkflow(id) {
    return this.request(`/workflows/${id}`);
  }

  async updateWorkflow(id, workflow) {
    return this.request(`/workflows/${id}`, {
      method: 'PUT',
      body: JSON.stringify(workflow),
    });
  }

  async deleteWorkflow(id) {
    return this.request(`/workflows/${id}`, {
      method: 'DELETE',
    });
  }

  // Workflow execution
  async executeWorkflow(id, inputData = {}) {
    return this.request(`/workflows/${id}/execute`, {
      method: 'POST',
      body: JSON.stringify({ input_data: inputData }),
    });
  }

  async getWorkflowRuns(id) {
    return this.request(`/workflows/${id}/runs`);
  }

  async getWorkflowRun(runId) {
    return this.request(`/workflow_runs/${runId}`);
  }

  // Workflow scheduling
  async createSchedule(workflowId, schedule) {
    return this.request(`/workflows/${workflowId}/schedules`, {
      method: 'POST',
      body: JSON.stringify(schedule),
    });
  }

  async getSchedules(workflowId) {
    return this.request(`/workflows/${workflowId}/schedules`);
  }

  async updateSchedule(scheduleId, schedule) {
    return this.request(`/schedules/${scheduleId}`, {
      method: 'PUT',
      body: JSON.stringify(schedule),
    });
  }

  async deleteSchedule(scheduleId) {
    return this.request(`/schedules/${scheduleId}`, {
      method: 'DELETE',
    });
  }

  async toggleSchedule(scheduleId) {
    return this.request(`/schedules/${scheduleId}/toggle`, {
      method: 'POST',
    });
  }

  // Workflow execution logs
  async getWorkflowExecutionLogs(workflowId, params = {}) {
    // Build query string from params
    const queryParams = new URLSearchParams();
    Object.keys(params).forEach(key => {
      if (params[key]) {
        queryParams.append(key, params[key]);
      }
    });
    
    const queryString = queryParams.toString();
    const endpoint = `/workflows/${workflowId}/logs${queryString ? '?' + queryString : ''}`;
    
    return this.request(endpoint);
  }

  async getExecutionLog(logId) {
    return this.request(`/logs/${logId}`);
  }

  async deleteExecutionLog(logId) {
    return this.request(`/logs/${logId}`, {
      method: 'DELETE',
    });
  }

  // Workflow sharing operations
  async shareWorkflow(workflowId, shareData) {
    return this.request(`/workflows/${workflowId}/share`, {
      method: 'POST',
      body: JSON.stringify(shareData),
    });
  }

  async getWorkflowShares(workflowId) {
    return this.request(`/workflows/${workflowId}/share`);
  }

  async updateWorkflowShare(workflowId, userId, shareData) {
    return this.request(`/workflows/${workflowId}/share/${userId}`, {
      method: 'PUT',
      body: JSON.stringify(shareData),
    });
  }

  async deleteWorkflowShare(workflowId, userId) {
    return this.request(`/workflows/${workflowId}/share/${userId}`, {
      method: 'DELETE',
    });
  }
}

export const workflowAPI = new WorkflowAPI();