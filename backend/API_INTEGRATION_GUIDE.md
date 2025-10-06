# WorkFlowN2N API Integration Guide

## Overview

This guide provides detailed information about integrating with the WorkFlowN2N API, with a focus on the workflow import/export functionality. The API enables external applications, plugins, and services to interact with workflow management features programmatically.

## Authentication

### Bearer Token Authentication

All API endpoints (except authentication endpoints) require Bearer token authentication:

```http
Authorization: Bearer <your_access_token>
```

### Obtaining Access Tokens

1. **Login Endpoint**: `POST /auth/login`
2. **Register Endpoint**: `POST /auth/register`

## Workflow Import/Export API

### Export Workflow

Export a single workflow in JSON or ZIP format.

**Endpoint**: `GET /workflows/{workflow_id}/export`

**Parameters**:
- `workflow_id` (path, required): The ID of the workflow to export
- `format` (query, optional): Export format (`json` or `zip`, default: `json`)

**Response Formats**:

#### JSON Format
```json
{
  "version": "1.0",
  "exported_at": "2024-01-15T10:30:00Z",
  "workflow": {
    "name": "Data Processing Pipeline",
    "description": "Automated data processing workflow",
    "nodes": [
      {
        "id": "1",
        "type": "input",
        "data": {
          "label": "Input Data",
          "config": {
            "input_type": "file"
          }
        },
        "position": {
          "x": 100,
          "y": 50
        }
      }
    ],
    "edges": [],
    "is_public": false,
    "created_at": "2024-01-01T00:00:00Z",
    "updated_at": "2024-01-10T15:30:00Z"
  },
  "metadata": {
    "exported_by": "john_doe",
    "workflow_id": 123,
    "owner": {
      "username": "john_doe",
      "email": "john@example.com"
    }
  }
}
```

#### ZIP Format
ZIP archives contain:
- `workflow_[name].json`: Main workflow JSON file
- `README.md`: Import instructions and metadata
- Additional documentation files

### Import Workflow

Import a workflow from a JSON or ZIP file.

**Endpoint**: `POST /workflows/import`

**Request Body** (multipart/form-data):
- `file` (required): The workflow file to import (JSON or ZIP)
- `name` (optional): New name for the imported workflow
- `description` (optional): New description for the imported workflow
- `make_public` (optional): Whether to make the workflow public (default: false)

**Response**:
```json
{
  "id": 456,
  "name": "My Imported Workflow",
  "description": "Imported from external source",
  "nodes": [],
  "edges": [],
  "owner_id": 789,
  "is_public": false,
  "created_at": "2024-01-15T10:35:00Z",
  "updated_at": "2024-01-15T10:35:00Z"
}
```

### Bulk Export Workflows

Export multiple workflows as a single ZIP archive.

**Endpoint**: `POST /workflows/bulk-export`

**Request Body**:
```json
{
  "workflow_ids": [123, 456, 789],
  "format": "zip"
}
```

**Response**: ZIP archive containing multiple workflow files with a manifest.

## Integration Examples

### JavaScript/Node.js Integration

```javascript
const axios = require('axios');
const fs = require('fs');
const FormData = require('form-data');

const API_BASE_URL = 'http://localhost:8000';
const TOKEN = 'your_access_token_here';

// Export workflow
async function exportWorkflow(workflowId, format = 'json') {
  try {
    const response = await axios.get(
      `${API_BASE_URL}/workflows/${workflowId}/export`,
      {
        params: { format },
        headers: {
          'Authorization': `Bearer ${TOKEN}`,
          'Accept': format === 'zip' ? 'application/zip' : 'application/json'
        },
        responseType: format === 'zip' ? 'arraybuffer' : 'json'
      }
    );
    
    if (format === 'zip') {
      fs.writeFileSync('exported_workflow.zip', response.data);
      console.log('Workflow exported as ZIP');
    } else {
      fs.writeFileSync('exported_workflow.json', JSON.stringify(response.data, null, 2));
      console.log('Workflow exported as JSON');
    }
    
    return response.data;
  } catch (error) {
    console.error('Export failed:', error.response?.data || error.message);
    throw error;
  }
}

// Import workflow
async function importWorkflow(filePath, options = {}) {
  try {
    const formData = new FormData();
    formData.append('file', fs.createReadStream(filePath));
    
    if (options.name) formData.append('name', options.name);
    if (options.description) formData.append('description', options.description);
    if (options.make_public) formData.append('make_public', options.make_public);
    
    const response = await axios.post(
      `${API_BASE_URL}/workflows/import`,
      formData,
      {
        headers: {
          'Authorization': `Bearer ${TOKEN}`,
          ...formData.getHeaders()
        }
      }
    );
    
    console.log('Workflow imported successfully:', response.data);
    return response.data;
  } catch (error) {
    console.error('Import failed:', error.response?.data || error.message);
    throw error;
  }
}

// Bulk export workflows
async function bulkExportWorkflows(workflowIds) {
  try {
    const response = await axios.post(
      `${API_BASE_URL}/workflows/bulk-export`,
      {
        workflow_ids: workflowIds,
        format: 'zip'
      },
      {
        headers: {
          'Authorization': `Bearer ${TOKEN}`,
          'Accept': 'application/zip'
        },
        responseType: 'arraybuffer'
      }
    );
    
    fs.writeFileSync('bulk_exported_workflows.zip', response.data);
    console.log('Bulk export completed');
    return response.data;
  } catch (error) {
    console.error('Bulk export failed:', error.response?.data || error.message);
    throw error;
  }
}

// Usage examples
exportWorkflow(123, 'json').then(data => {
  console.log('Export completed:', data);
});

importWorkflow('./workflow.json', {
  name: 'My New Workflow',
  description: 'Imported from external system'
}).then(workflow => {
  console.log('Import completed:', workflow);
});

bulkExportWorkflows([123, 456, 789]).then(() => {
  console.log('Bulk export completed');
});
```

### Python Integration

```python
import requests
import json
import zipfile
import io

API_BASE_URL = "http://localhost:8000"
TOKEN = "your_access_token_here"

headers = {
    "Authorization": f"Bearer {TOKEN}"
}

def export_workflow(workflow_id, format="json"):
    """Export a workflow in JSON or ZIP format"""
    url = f"{API_BASE_URL}/workflows/{workflow_id}/export"
    params = {"format": format}
    
    response = requests.get(url, params=params, headers=headers)
    
    if response.status_code == 200:
        if format == "zip":
            with open("exported_workflow.zip", "wb") as f:
                f.write(response.content)
            print("Workflow exported as ZIP")
        else:
            with open("exported_workflow.json", "w") as f:
                json.dump(response.json(), f, indent=2)
            print("Workflow exported as JSON")
        return response.content if format == "zip" else response.json()
    else:
        raise Exception(f"Export failed: {response.text}")

def import_workflow(file_path, name=None, description=None, make_public=False):
    """Import a workflow from a file"""
    url = f"{API_BASE_URL}/workflows/import"
    
    files = {"file": open(file_path, "rb")}
    data = {}
    
    if name:
        data["name"] = name
    if description:
        data["description"] = description
    if make_public:
        data["make_public"] = "true"
    
    response = requests.post(url, files=files, data=data, headers=headers)
    
    if response.status_code == 200:
        print("Workflow imported successfully")
        return response.json()
    else:
        raise Exception(f"Import failed: {response.text}")

def bulk_export_workflows(workflow_ids):
    """Bulk export multiple workflows"""
    url = f"{API_BASE_URL}/workflows/bulk-export"
    data = {
        "workflow_ids": workflow_ids,
        "format": "zip"
    }
    
    response = requests.post(url, json=data, headers=headers)
    
    if response.status_code == 200:
        with open("bulk_exported_workflows.zip", "wb") as f:
            f.write(response.content)
        print("Bulk export completed")
        return response.content
    else:
        raise Exception(f"Bulk export failed: {response.text}")

# Usage examples
workflow_data = export_workflow(123, "json")
print("Export completed:", workflow_data)

imported_workflow = import_workflow(
    "./workflow.json",
    name="My New Workflow",
    description="Imported from external system"
)
print("Import completed:", imported_workflow)

bulk_export_workflows([123, 456, 789])
print("Bulk export completed")
```

### cURL Examples

```bash
# Export workflow as JSON
curl -X GET "http://localhost:8000/workflows/123/export?format=json" \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Accept: application/json" \
  -o exported_workflow.json

# Export workflow as ZIP
curl -X GET "http://localhost:8000/workflows/123/export?format=zip" \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Accept: application/zip" \
  -o exported_workflow.zip

# Import workflow from JSON file
curl -X POST "http://localhost:8000/workflows/import" \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -F "file=@workflow.json" \
  -F "name=My Imported Workflow" \
  -F "description=Imported from external system" \
  -F "make_public=false"

# Bulk export workflows
curl -X POST "http://localhost:8000/workflows/bulk-export" \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -H "Accept: application/zip" \
  -d '{"workflow_ids": [123, 456, 789], "format": "zip"}' \
  -o bulk_exported_workflows.zip
```

## Error Handling

The API returns standard HTTP status codes and JSON error responses:

```json
{
  "detail": "Error message describing what went wrong"
}
```

### Common Error Codes

- `400 Bad Request`: Invalid parameters or file format
- `403 Forbidden`: Insufficient permissions
- `404 Not Found`: Workflow not found
- `422 Unprocessable Entity`: Validation errors
- `500 Internal Server Error`: Server-side errors

### Error Response Examples

```json
// Invalid file format
{
  "detail": "File must be JSON or ZIP format"
}

// Missing required field
{
  "detail": "Missing required field: name"
}

// Unsupported version
{
  "detail": "Unsupported version: 2.0"
}

// Permission denied
{
  "detail": "Not authorized to create workflows"
}
```

## File Format Specifications

### JSON Workflow Format

```json
{
  "name": "string (required)",
  "description": "string (optional)",
  "nodes": [
    {
      "id": "string (required)",
      "type": "string (required)",
      "data": {
        "label": "string (required)",
        "config": "object (optional)"
      },
      "position": {
        "x": "number (required)",
        "y": "number (required)"
      }
    }
  ],
  "edges": [
    {
      "id": "string (required)",
      "source": "string (required)",
      "target": "string (required)",
      "sourceHandle": "string (optional)",
      "targetHandle": "string (optional)"
    }
  ],
  "is_public": "boolean (default: false)"
}
```

### ZIP Archive Structure

```
workflow_export_[name]_[timestamp].zip
├── workflow_[name].json      # Main workflow JSON file
├── README.md                # Import instructions
└── manifest.json            # Bulk export manifest (for bulk exports)
```

## Best Practices

### Security Considerations

1. **Token Management**: Store tokens securely and implement token refresh logic
2. **File Validation**: Validate file types and content before processing
3. **Error Handling**: Implement comprehensive error handling and user feedback
4. **Rate Limiting**: Implement client-side rate limiting for API calls

### Performance Optimization

1. **Batch Operations**: Use bulk export for multiple workflows
2. **File Compression**: Use ZIP format for large workflows
3. **Async Processing**: Implement async processing for large imports
4. **Caching**: Cache exported workflows when possible

### Integration Tips

1. **Version Compatibility**: Check API version compatibility
2. **Field Validation**: Validate required fields before import
3. **User Feedback**: Provide clear feedback during import/export operations
4. **Progress Indicators**: Show progress for long-running operations

## Plugin Development

The import/export API can be used by plugins to:

1. **Backup Workflows**: Create automated backup systems
2. **Migration Tools**: Migrate workflows between instances
3. **Template Systems**: Create and share workflow templates
4. **Integration Tools**: Integrate with external systems

### Plugin API Usage

```javascript
// Plugin example for workflow backup
class WorkflowBackupPlugin {
  constructor(apiClient) {
    this.api = apiClient;
  }
  
  async backupWorkflow(workflowId, backupName) {
    try {
      const workflowData = await this.api.exportWorkflow(workflowId, 'json');
      const backup = {
        ...workflowData,
        backup_info: {
          backup_name: backupName,
          backup_date: new Date().toISOString(),
          plugin_version: "1.0.0"
        }
      };
      
      // Store backup in plugin storage
      await this.storeBackup(backup);
      return backup;
    } catch (error) {
      console.error('Backup failed:', error);
      throw error;
    }
  }
  
  async restoreWorkflow(backupId, options = {}) {
    try {
      const backup = await this.getBackup(backupId);
      const { workflow } = backup;
      
      // Restore workflow using import API
      const imported = await this.api.importWorkflow(
        this.createFileFromData(workflow),
        options.name || workflow.name,
        options.description || workflow.description,
        options.make_public || workflow.is_public
      );
      
      return imported;
    } catch (error) {
      console.error('Restore failed:', error);
      throw error;
    }
  }
}
```

## Troubleshooting

### Common Issues

1. **File Upload Failures**: Check file size limits and network connectivity
2. **Import Validation Errors**: Verify JSON structure and required fields
3. **Permission Errors**: Ensure proper authentication and user permissions
4. **Version Compatibility**: Check API version and workflow format version

### Debug Information

Enable debug logging in your integration:

```javascript
const axios = require('axios');

// Enable request/response logging
axios.interceptors.request.use(request => {
  console.log('Starting Request', {
    url: request.url,
    method: request.method,
    headers: request.headers
  });
  return request;
});

axios.interceptors.response.use(response => {
  console.log('Response:', {
    status: response.status,
    data: response.data
  });
  return response;
});
```

## Support

For API support and questions:

- **Documentation**: [API Documentation](http://localhost:8000/docs)
- **Issues**: Report issues on the project repository
- **Contact**: support@workflown2n.com

## Version History

- **v1.0.0**: Initial release with import/export functionality
- **v1.0.1**: Added bulk export support
- **v1.0.2**: Enhanced error handling and validation