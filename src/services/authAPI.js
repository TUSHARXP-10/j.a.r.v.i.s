// Authentication API service
const API_BASE_URL = 'http://localhost:8000';

class AuthAPI {
  constructor() {
    this.baseUrl = API_BASE_URL;
  }

  // Set auth token for requests
  setToken(token) {
    this.token = token;
  }

  // Clear auth token
  clearToken() {
    this.token = null;
  }

  // Make authenticated request
  async request(endpoint, options = {}) {
    const url = `${this.baseUrl}${endpoint}`;
    const config = {
      headers: {
        'Content-Type': 'application/json',
        ...options.headers,
      },
      ...options,
    };

    // Add auth token if available
    if (this.token) {
      config.headers['Authorization'] = `Bearer ${this.token}`;
    }

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

  // Authentication endpoints
  async login(username, password) {
    const response = await this.request('/auth/login', {
      method: 'POST',
      body: JSON.stringify({ username, password }),
    });
    
    // Set token for future requests
    if (response.access_token) {
      this.setToken(response.access_token);
    }
    
    return response;
  }

  async register(userData) {
    const response = await this.request('/auth/register', {
      method: 'POST',
      body: JSON.stringify(userData),
    });
    
    // Set token for future requests
    if (response.access_token) {
      this.setToken(response.access_token);
    }
    
    return response;
  }

  async getCurrentUser() {
    return this.request('/auth/me');
  }

  // User management endpoints (admin only)
  async getUsers() {
    return this.request('/admin/users');
  }

  async createUser(userData) {
    return this.request('/auth/register', {
      method: 'POST',
      body: JSON.stringify(userData),
    });
  }

  async updateUserRole(userId, role) {
    return this.request(`/admin/users/${userId}/role?role=${role}`, {
      method: 'PUT',
    });
  }

  async toggleUserStatus(userId, isActive) {
    return this.request(`/admin/users/${userId}/status`, {
      method: 'PUT',
      body: JSON.stringify({ is_active: isActive }),
    });
  }

  // Workflow API wrapper with auth
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

  // Workflow execution with auth
  async executeWorkflow(id, inputData = {}) {
    return this.request(`/workflows/${id}/execute`, {
      method: 'POST',
      body: JSON.stringify({ input_data: inputData }),
    });
  }

  async getWorkflowRuns(id) {
    return this.request(`/workflows/${id}/runs`);
  }

  // Workflow scheduling with auth
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

  // Workflow execution logs with auth
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
}

export const authAPI = new AuthAPI();