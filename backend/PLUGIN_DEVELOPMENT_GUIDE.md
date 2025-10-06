# Plugin Development Guide for WorkFlowN2N Import/Export

## Overview

This guide provides comprehensive information for developing plugins that integrate with the WorkFlowN2N import/export functionality. Plugins can extend the system's capabilities for backup, migration, template management, and external system integration.

## Plugin Architecture

### Plugin Types

1. **Backup Plugins**: Automated workflow backup and restore
2. **Migration Plugins**: Transfer workflows between instances
3. **Template Plugins**: Create and manage workflow templates
4. **Integration Plugins**: Connect with external systems
5. **Export Plugins**: Custom export formats and destinations

### Plugin Structure

```javascript
// Base plugin structure
class WorkflowPlugin {
  constructor(config) {
    this.config = config;
    this.api = new WorkflowAPI(config.apiUrl, config.token);
    this.name = 'Plugin Name';
    this.version = '1.0.0';
    this.description = 'Plugin description';
  }
  
  async initialize() {
    // Plugin initialization logic
  }
  
  async cleanup() {
    // Plugin cleanup logic
  }
  
  getInfo() {
    return {
      name: this.name,
      version: this.version,
      description: this.description
    };
  }
}
```

## API Integration

### WorkflowAPI Class

```javascript
class WorkflowAPI {
  constructor(baseUrl, token) {
    this.baseUrl = baseUrl;
    this.token = token;
  }
  
  async exportWorkflow(workflowId, format = 'json') {
    const response = await fetch(`${this.baseUrl}/workflows/${workflowId}/export?format=${format}`, {
      headers: {
        'Authorization': `Bearer ${this.token}`,
        'Accept': format === 'zip' ? 'application/zip' : 'application/json'
      }
    });
    
    if (!response.ok) {
      throw new Error(`Export failed: ${response.statusText}`);
    }
    
    return format === 'zip' ? response.arrayBuffer() : response.json();
  }
  
  async importWorkflow(file, options = {}) {
    const formData = new FormData();
    formData.append('file', file);
    
    if (options.name) formData.append('name', options.name);
    if (options.description) formData.append('description', options.description);
    if (options.make_public) formData.append('make_public', options.make_public);
    
    const response = await fetch(`${this.baseUrl}/workflows/import`, {
      method: 'POST',
      headers: {
        'Authorization': `Bearer ${this.token}`
      },
      body: formData
    });
    
    if (!response.ok) {
      throw new Error(`Import failed: ${response.statusText}`);
    }
    
    return response.json();
  }
  
  async bulkExportWorkflows(workflowIds) {
    const response = await fetch(`${this.baseUrl}/workflows/bulk-export`, {
      method: 'POST',
      headers: {
        'Authorization': `Bearer ${this.token}`,
        'Content-Type': 'application/json',
        'Accept': 'application/zip'
      },
      body: JSON.stringify({
        workflow_ids: workflowIds,
        format: 'zip'
      })
    });
    
    if (!response.ok) {
      throw new Error(`Bulk export failed: ${response.statusText}`);
    }
    
    return response.arrayBuffer();
  }
}
```

## Plugin Examples

### 1. Automated Backup Plugin

```javascript
class AutomatedBackupPlugin extends WorkflowPlugin {
  constructor(config) {
    super(config);
    this.name = 'Automated Backup Plugin';
    this.version = '1.0.0';
    this.description = 'Automatically backs up workflows on schedule';
    this.backupSchedule = config.backupSchedule || '0 2 * * *'; // Daily at 2 AM
    this.retentionDays = config.retentionDays || 30;
    this.storageBackend = config.storageBackend || 'local';
  }
  
  async initialize() {
    // Set up scheduled backup
    this.scheduleBackup();
    console.log('Automated backup plugin initialized');
  }
  
  async scheduleBackup() {
    // Use node-cron or similar for scheduling
    const cron = require('node-cron');
    
    cron.schedule(this.backupSchedule, async () => {
      console.log('Running scheduled backup...');
      await this.performBackup();
    });
  }
  
  async performBackup() {
    try {
      // Get all workflows (you'll need to implement this method)
      const workflows = await this.getAllWorkflows();
      
      for (const workflow of workflows) {
        const backupData = await this.createBackup(workflow);
        await this.storeBackup(backupData);
      }
      
      console.log(`Backup completed for ${workflows.length} workflows`);
    } catch (error) {
      console.error('Backup failed:', error);
      this.notifyError('Backup failed', error.message);
    }
  }
  
  async createBackup(workflow) {
    const exportData = await this.api.exportWorkflow(workflow.id, 'json');
    
    return {
      workflow_id: workflow.id,
      workflow_name: workflow.name,
      backup_date: new Date().toISOString(),
      export_data: exportData,
      plugin_version: this.version,
      backup_type: 'automated'
    };
  }
  
  async storeBackup(backupData) {
    switch (this.storageBackend) {
      case 'local':
        await this.storeLocal(backupData);
        break;
      case 's3':
        await this.storeS3(backupData);
        break;
      case 'azure':
        await this.storeAzure(backupData);
        break;
      default:
        throw new Error(`Unknown storage backend: ${this.storageBackend}`);
    }
  }
  
  async storeLocal(backupData) {
    const fs = require('fs').promises;
    const path = require('path');
    
    const backupDir = path.join(process.cwd(), 'backups');
    await fs.mkdir(backupDir, { recursive: true });
    
    const filename = `backup_${backupData.workflow_id}_${Date.now()}.json`;
    const filepath = path.join(backupDir, filename);
    
    await fs.writeFile(filepath, JSON.stringify(backupData, null, 2));
    console.log(`Backup stored locally: ${filename}`);
  }
  
  async restoreFromBackup(backupId, options = {}) {
    try {
      const backupData = await this.getBackup(backupId);
      const { export_data } = backupData;
      
      // Create file from export data
      const file = this.createFileFromData(export_data.workflow);
      
      // Import workflow
      const importedWorkflow = await this.api.importWorkflow(file, {
        name: options.name || `${export_data.workflow.name} (Restored)`,
        description: options.description || `Restored from backup: ${backupData.backup_date}`,
        make_public: options.make_public || export_data.workflow.is_public
      });
      
      console.log(`Workflow restored: ${importedWorkflow.name}`);
      return importedWorkflow;
    } catch (error) {
      console.error('Restore failed:', error);
      throw error;
    }
  }
  
  notifyError(title, message) {
    // Implement notification system (email, Slack, etc.)
    console.error(`[${title}] ${message}`);
  }
}
```

### 2. Migration Plugin

```javascript
class MigrationPlugin extends WorkflowPlugin {
  constructor(config) {
    super(config);
    this.name = 'Workflow Migration Plugin';
    this.version = '1.0.0';
    this.description = 'Migrate workflows between WorkFlowN2N instances';
    this.sourceUrl = config.sourceUrl;
    this.sourceToken = config.sourceToken;
    this.targetUrl = config.targetUrl;
    this.targetToken = config.targetToken;
  }
  
  async migrateWorkflow(workflowId, options = {}) {
    try {
      console.log(`Starting migration for workflow ${workflowId}...`);
      
      // Create source API client
      const sourceAPI = new WorkflowAPI(this.sourceUrl, this.sourceToken);
      
      // Export from source
      const exportData = await sourceAPI.exportWorkflow(workflowId, 'json');
      console.log('Workflow exported from source');
      
      // Create target API client
      const targetAPI = new WorkflowAPI(this.targetUrl, this.targetToken);
      
      // Create file from export data
      const file = this.createFileFromData(exportData.workflow);
      
      // Import to target
      const importOptions = {
        name: options.name || exportData.workflow.name,
        description: options.description || `${exportData.workflow.description} (Migrated from ${this.sourceUrl})`,
        make_public: options.make_public || exportData.workflow.is_public
      };
      
      const importedWorkflow = await targetAPI.importWorkflow(file, importOptions);
      
      console.log(`Workflow migrated successfully: ${importedWorkflow.name}`);
      
      return {
        source_workflow_id: workflowId,
        target_workflow_id: importedWorkflow.id,
        workflow_name: importedWorkflow.name,
        migration_date: new Date().toISOString(),
        source_url: this.sourceUrl,
        target_url: this.targetUrl
      };
    } catch (error) {
      console.error('Migration failed:', error);
      throw new Error(`Migration failed for workflow ${workflowId}: ${error.message}`);
    }
  }
  
  async bulkMigrateWorkflows(workflowIds, options = {}) {
    const results = [];
    const errors = [];
    
    for (const workflowId of workflowIds) {
      try {
        const result = await this.migrateWorkflow(workflowId, options);
        results.push(result);
      } catch (error) {
        errors.push({
          workflow_id: workflowId,
          error: error.message
        });
      }
    }
    
    return {
      successful: results,
      failed: errors,
      total_processed: workflowIds.length,
      successful_count: results.length,
      failed_count: errors.length
    };
  }
  
  async validateMigration(workflowId) {
    try {
      const sourceAPI = new WorkflowAPI(this.sourceUrl, this.sourceToken);
      const targetAPI = new WorkflowAPI(this.targetUrl, this.targetToken);
      
      // Export from source
      const sourceExport = await sourceAPI.exportWorkflow(workflowId, 'json');
      
      // Check if workflow already exists in target
      // (You'd need to implement workflow listing in the API)
      const existingWorkflows = await this.listWorkflows(targetAPI);
      const existingWorkflow = existingWorkflows.find(w => w.name === sourceExport.workflow.name);
      
      return {
        can_migrate: true,
        workflow_exists: !!existingWorkflow,
        existing_workflow_id: existingWorkflow?.id,
        workflow_size: JSON.stringify(sourceExport).length,
        source_workflow: {
          name: sourceExport.workflow.name,
          node_count: sourceExport.workflow.nodes.length,
          edge_count: sourceExport.workflow.edges.length,
          created_at: sourceExport.workflow.created_at,
          updated_at: sourceExport.workflow.updated_at
        }
      };
    } catch (error) {
      return {
        can_migrate: false,
        error: error.message
      };
    }
  }
  
  createFileFromData(data) {
    const jsonString = JSON.stringify(data, null, 2);
    const blob = new Blob([jsonString], { type: 'application/json' });
    return new File([blob], 'workflow.json', { type: 'application/json' });
  }
}
```

### 3. Template Management Plugin

```javascript
class TemplatePlugin extends WorkflowPlugin {
  constructor(config) {
    super(config);
    this.name = 'Workflow Template Plugin';
    this.version = '1.0.0';
    this.description = 'Create and manage workflow templates';
    this.templateCategories = config.categories || ['data-processing', 'automation', 'integration'];
    this.templateStorage = config.storage || 'local';
  }
  
  async createTemplate(workflowId, templateInfo) {
    try {
      // Export workflow
      const exportData = await this.api.exportWorkflow(workflowId, 'json');
      
      // Create template
      const template = {
        id: this.generateTemplateId(),
        name: templateInfo.name,
        description: templateInfo.description,
        category: templateInfo.category,
        tags: templateInfo.tags || [],
        workflow_data: exportData.workflow,
        metadata: {
          original_workflow_id: workflowId,
          created_at: new Date().toISOString(),
          updated_at: new Date().toISOString(),
          plugin_version: this.version,
          template_version: '1.0.0',
          usage_count: 0,
          rating: 0,
          author: templateInfo.author || 'anonymous'
        }
      };
      
      // Store template
      await this.storeTemplate(template);
      
      console.log(`Template created: ${template.name}`);
      return template;
    } catch (error) {
      console.error('Template creation failed:', error);
      throw error;
    }
  }
  
  async instantiateTemplate(templateId, options = {}) {
    try {
      // Get template
      const template = await this.getTemplate(templateId);
      
      // Create file from template data
      const file = this.createFileFromData(template.workflow_data);
      
      // Import workflow
      const importOptions = {
        name: options.name || `${template.name} (From Template)`,
        description: options.description || `Created from template: ${template.name}`,
        make_public: options.make_public || false
      };
      
      const importedWorkflow = await this.api.importWorkflow(file, importOptions);
      
      // Update template usage count
      await this.updateTemplateUsage(templateId);
      
      console.log(`Template instantiated: ${importedWorkflow.name}`);
      return importedWorkflow;
    } catch (error) {
      console.error('Template instantiation failed:', error);
      throw error;
    }
  }
  
  async searchTemplates(query, filters = {}) {
    try {
      const templates = await this.getAllTemplates();
      
      let results = templates;
      
      // Filter by query
      if (query) {
        results = results.filter(template => 
          template.name.toLowerCase().includes(query.toLowerCase()) ||
          template.description.toLowerCase().includes(query.toLowerCase()) ||
          template.tags.some(tag => tag.toLowerCase().includes(query.toLowerCase()))
        );
      }
      
      // Filter by category
      if (filters.category) {
        results = results.filter(template => template.category === filters.category);
      }
      
      // Filter by tags
      if (filters.tags && filters.tags.length > 0) {
        results = results.filter(template => 
          filters.tags.some(tag => template.tags.includes(tag))
        );
      }
      
      // Sort by usage count or rating
      if (filters.sortBy) {
        results.sort((a, b) => {
          switch (filters.sortBy) {
            case 'usage':
              return b.metadata.usage_count - a.metadata.usage_count;
            case 'rating':
              return b.metadata.rating - a.metadata.rating;
            case 'created':
              return new Date(b.metadata.created_at) - new Date(a.metadata.created_at);
            default:
              return 0;
          }
        });
      }
      
      return results;
    } catch (error) {
      console.error('Template search failed:', error);
      throw error;
    }
  }
  
  generateTemplateId() {
    return `template_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`;
  }
  
  async storeTemplate(template) {
    switch (this.templateStorage) {
      case 'local':
        await this.storeLocalTemplate(template);
        break;
      case 'database':
        await this.storeDatabaseTemplate(template);
        break;
      case 'cloud':
        await this.storeCloudTemplate(template);
        break;
      default:
        throw new Error(`Unknown storage backend: ${this.templateStorage}`);
    }
  }
  
  async storeLocalTemplate(template) {
    const fs = require('fs').promises;
    const path = require('path');
    
    const templateDir = path.join(process.cwd(), 'templates');
    await fs.mkdir(templateDir, { recursive: true });
    
    const filepath = path.join(templateDir, `${template.id}.json`);
    await fs.writeFile(filepath, JSON.stringify(template, null, 2));
    
    console.log(`Template stored locally: ${template.name}`);
  }
}
```

## Plugin Development Best Practices

### 1. Error Handling

```javascript
class RobustPlugin extends WorkflowPlugin {
  async safeOperation(operation, ...args) {
    try {
      return await operation(...args);
    } catch (error) {
      this.handleError(error);
      throw error;
    }
  }
  
  handleError(error) {
    console.error('Plugin error:', error);
    
    // Log to file
    this.logError(error);
    
    // Send notification
    this.notifyError(error);
    
    // Attempt recovery if possible
    this.attemptRecovery(error);
  }
  
  logError(error) {
    const fs = require('fs');
    const logEntry = {
      timestamp: new Date().toISOString(),
      plugin: this.name,
      version: this.version,
      error: error.message,
      stack: error.stack
    };
    
    fs.appendFileSync('plugin-errors.log', JSON.stringify(logEntry) + '\n');
  }
  
  notifyError(error) {
    // Implement notification system
    console.error(`[${this.name}] ${error.message}`);
  }
  
  attemptRecovery(error) {
    // Implement recovery logic based on error type
    console.log('Attempting recovery...');
  }
}
```

### 2. Configuration Management

```javascript
class ConfigurablePlugin extends WorkflowPlugin {
  constructor(config) {
    super(config);
    this.configSchema = {
      apiUrl: { type: 'string', required: true },
      token: { type: 'string', required: true },
      retryAttempts: { type: 'number', default: 3 },
      retryDelay: { type: 'number', default: 1000 },
      timeout: { type: 'number', default: 30000 },
      storageBackend: { type: 'string', default: 'local' }
    };
    
    this.validateConfig(config);
    this.config = { ...this.getDefaultConfig(), ...config };
  }
  
  validateConfig(config) {
    for (const [key, schema] of Object.entries(this.configSchema)) {
      if (schema.required && !config[key]) {
        throw new Error(`Missing required config: ${key}`);
      }
      
      if (config[key] && typeof config[key] !== schema.type) {
        throw new Error(`Invalid config type for ${key}: expected ${schema.type}, got ${typeof config[key]}`);
      }
    }
  }
  
  getDefaultConfig() {
    const defaults = {};
    for (const [key, schema] of Object.entries(this.configSchema)) {
      if (schema.default !== undefined) {
        defaults[key] = schema.default;
      }
    }
    return defaults;
  }
  
  updateConfig(newConfig) {
    this.validateConfig(newConfig);
    this.config = { ...this.config, ...newConfig };
    this.onConfigUpdate();
  }
  
  onConfigUpdate() {
    // Handle config updates
    console.log('Plugin configuration updated');
  }
}
```

### 3. Monitoring and Metrics

```javascript
class MonitoredPlugin extends WorkflowPlugin {
  constructor(config) {
    super(config);
    this.metrics = {
      operations_total: 0,
      operations_successful: 0,
      operations_failed: 0,
      operation_duration: [],
      last_operation_time: null
    };
  }
  
  async trackOperation(operation, name, ...args) {
    const startTime = Date.now();
    this.metrics.operations_total++;
    
    try {
      const result = await operation(...args);
      this.metrics.operations_successful++;
      return result;
    } catch (error) {
      this.metrics.operations_failed++;
      throw error;
    } finally {
      const duration = Date.now() - startTime;
      this.metrics.operation_duration.push(duration);
      this.metrics.last_operation_time = new Date().toISOString();
      
      // Keep only last 100 durations
      if (this.metrics.operation_duration.length > 100) {
        this.metrics.operation_duration = this.metrics.operation_duration.slice(-100);
      }
    }
  }
  
  getMetrics() {
    const avgDuration = this.metrics.operation_duration.length > 0 
      ? this.metrics.operation_duration.reduce((a, b) => a + b, 0) / this.metrics.operation_duration.length
      : 0;
    
    return {
      ...this.metrics,
      success_rate: this.metrics.operations_total > 0 
        ? (this.metrics.operations_successful / this.metrics.operations_total) * 100 
        : 0,
      average_duration: avgDuration
    };
  }
  
  resetMetrics() {
    this.metrics = {
      operations_total: 0,
      operations_successful: 0,
      operations_failed: 0,
      operation_duration: [],
      last_operation_time: null
    };
  }
}
```

## Plugin Registration and Management

### Plugin Registration System

```javascript
class PluginManager {
  constructor() {
    this.plugins = new Map();
    this.pluginConfigs = new Map();
  }
  
  registerPlugin(name, pluginClass, config = {}) {
    if (this.plugins.has(name)) {
      throw new Error(`Plugin ${name} is already registered`);
    }
    
    try {
      const plugin = new pluginClass(config);
      this.plugins.set(name, plugin);
      this.pluginConfigs.set(name, config);
      
      console.log(`Plugin registered: ${name}`);
      return plugin;
    } catch (error) {
      console.error(`Failed to register plugin ${name}:`, error);
      throw error;
    }
  }
  
  unregisterPlugin(name) {
    const plugin = this.plugins.get(name);
    if (plugin) {
      plugin.cleanup();
      this.plugins.delete(name);
      this.pluginConfigs.delete(name);
      console.log(`Plugin unregistered: ${name}`);
    }
  }
  
  getPlugin(name) {
    return this.plugins.get(name);
  }
  
  getAllPlugins() {
    return Array.from(this.plugins.values());
  }
  
  async initializeAll() {
    for (const [name, plugin] of this.plugins) {
      try {
        await plugin.initialize();
        console.log(`Plugin initialized: ${name}`);
      } catch (error) {
        console.error(`Failed to initialize plugin ${name}:`, error);
      }
    }
  }
  
  async cleanupAll() {
    for (const [name, plugin] of this.plugins) {
      try {
        await plugin.cleanup();
        console.log(`Plugin cleaned up: ${name}`);
      } catch (error) {
        console.error(`Failed to cleanup plugin ${name}:`, error);
      }
    }
  }
}

// Usage
const pluginManager = new PluginManager();

// Register plugins
pluginManager.registerPlugin('backup', AutomatedBackupPlugin, {
  apiUrl: 'http://localhost:8000',
  token: 'your_token_here',
  backupSchedule: '0 2 * * *',
  retentionDays: 30,
  storageBackend: 'local'
});

pluginManager.registerPlugin('migration', MigrationPlugin, {
  apiUrl: 'http://localhost:8000',
  token: 'your_token_here',
  sourceUrl: 'http://source-instance:8000',
  sourceToken: 'source_token',
  targetUrl: 'http://target-instance:8000',
  targetToken: 'target_token'
});

// Initialize all plugins
pluginManager.initializeAll();
```

## Testing Plugins

### Unit Testing

```javascript
// test/backup-plugin.test.js
const { AutomatedBackupPlugin } = require('../plugins/AutomatedBackupPlugin');
const { WorkflowAPI } = require('../api/WorkflowAPI');

describe('AutomatedBackupPlugin', () => {
  let plugin;
  let mockAPI;
  
  beforeEach(() => {
    mockAPI = {
      exportWorkflow: jest.fn().mockResolvedValue({
        workflow: {
          id: 123,
          name: 'Test Workflow',
          nodes: [],
          edges: []
        }
      })
    };
    
    plugin = new AutomatedBackupPlugin({
      api: mockAPI,
      backupSchedule: '0 2 * * *',
      retentionDays: 30
    });
  });
  
  test('should create backup successfully', async () => {
    const workflow = { id: 123, name: 'Test Workflow' };
    
    const backup = await plugin.createBackup(workflow);
    
    expect(backup).toHaveProperty('workflow_id', 123);
    expect(backup).toHaveProperty('workflow_name', 'Test Workflow');
    expect(backup).toHaveProperty('backup_date');
    expect(backup).toHaveProperty('export_data');
    expect(mockAPI.exportWorkflow).toHaveBeenCalledWith(123, 'json');
  });
  
  test('should handle backup errors', async () => {
    mockAPI.exportWorkflow.mockRejectedValue(new Error('Export failed'));
    
    const workflow = { id: 123, name: 'Test Workflow' };
    
    await expect(plugin.createBackup(workflow)).rejects.toThrow('Export failed');
  });
});
```

### Integration Testing

```javascript
// test/integration.test.js
const { PluginManager } = require('../plugins/PluginManager');
const { AutomatedBackupPlugin } = require('../plugins/AutomatedBackupPlugin');

describe('Plugin Integration', () => {
  let pluginManager;
  
  beforeEach(() => {
    pluginManager = new PluginManager();
  });
  
  test('should register and initialize plugin', async () => {
    const plugin = pluginManager.registerPlugin('backup', AutomatedBackupPlugin, {
      apiUrl: 'http://localhost:8000',
      token: 'test_token',
      backupSchedule: '0 2 * * *'
    });
    
    expect(pluginManager.getPlugin('backup')).toBe(plugin);
    expect(plugin.name).toBe('Automated Backup Plugin');
  });
  
  test('should handle plugin registration errors', () => {
    expect(() => {
      pluginManager.registerPlugin('backup', AutomatedBackupPlugin, {
        // Missing required config
      });
    }).toThrow();
  });
});
```

## Deployment and Distribution

### Plugin Packaging

```json
// plugin-package.json
{
  "name": "workflown2n-backup-plugin",
  "version": "1.0.0",
  "description": "Automated backup plugin for WorkFlowN2N",
  "main": "index.js",
  "scripts": {
    "test": "jest",
    "build": "webpack",
    "package": "npm run build && npm pack"
  },
  "dependencies": {
    "axios": "^1.0.0",
    "node-cron": "^3.0.0",
    "winston": "^3.0.0"
  },
  "peerDependencies": {
    "workflown2n-api": "^1.0.0"
  },
  "plugin": {
    "type": "backup",
    "api_version": "1.0.0",
    "config_schema": {
      "backupSchedule": {
        "type": "string",
        "default": "0 2 * * *",
        "description": "Cron schedule for automated backups"
      },
      "retentionDays": {
        "type": "number",
        "default": 30,
        "description": "Number of days to retain backups"
      }
    }
  }
}
```

### Plugin Installation

```bash
# Install plugin
npm install workflown2n-backup-plugin

# Configure plugin
cat > plugin-config.json << EOF
{
  "backup": {
    "backupSchedule": "0 2 * * *",
    "retentionDays": 30,
    "storageBackend": "local"
  }
}
EOF

# Run with plugins
node app.js --plugins backup --plugin-config plugin-config.json
```

This comprehensive plugin development guide provides everything needed to create robust plugins that integrate with the WorkFlowN2N import/export functionality. The examples demonstrate real-world use cases and best practices for building maintainable, scalable plugins.