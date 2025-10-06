# WorkFlowN2N OpenAPI Specifications

## Overview

This directory contains the OpenAPI 3.0.3 specifications for the WorkFlowN2N API, with a focus on the workflow import/export functionality. The specifications provide a comprehensive reference for integrating with the WorkFlowN2N platform.

## Files

- **`openapi.yaml`** - Main OpenAPI specification file
- **`API_INTEGRATION_GUIDE.md`** - Detailed integration guide with examples
- **`PLUGIN_DEVELOPMENT_GUIDE.md`** - Plugin development guide for extending functionality

## Quick Start

### Viewing the API Documentation

The OpenAPI specification can be viewed using various tools:

1. **Swagger Editor**: https://editor.swagger.io/
2. **Swagger UI**: https://swagger.io/tools/swagger-ui/
3. **Redoc**: https://redocly.github.io/redoc/
4. **Postman**: Import the YAML file directly

### Testing the API

1. **Using Swagger UI**:
   ```bash
   # Install Swagger UI
   npm install -g swagger-ui-dist
   
   # Serve the specification
   swagger-ui-serve openapi.yaml
   ```

2. **Using Redoc**:
   ```bash
   # Install Redoc CLI
   npm install -g redoc-cli
   
   # Build and serve
   redoc-cli serve openapi.yaml
   ```

## API Endpoints

### Workflow Import/Export

#### Export Workflow
```http
GET /workflows/{workflow_id}/export?format={json|zip}
```

Export a single workflow in JSON or ZIP format.

**Example Request**:
```bash
curl -X GET "http://localhost:8000/workflows/123/export?format=json" \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Accept: application/json"
```

**Example Response** (JSON):
```json
{
  "version": "1.0",
  "exported_at": "2024-01-15T10:30:00Z",
  "workflow": {
    "name": "Data Processing Pipeline",
    "description": "Automated data processing workflow",
    "nodes": [...],
    "edges": [...],
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

#### Import Workflow
```http
POST /workflows/import
```

Import a workflow from a JSON or ZIP file.

**Example Request**:
```bash
curl -X POST "http://localhost:8000/workflows/import" \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -F "file=@workflow.json" \
  -F "name=My Imported Workflow" \
  -F "description=Imported from external system" \
  -F "make_public=false"
```

**Example Response**:
```json
{
  "id": 456,
  "name": "My Imported Workflow",
  "description": "Imported from external system",
  "nodes": [],
  "edges": [],
  "owner_id": 789,
  "is_public": false,
  "created_at": "2024-01-15T10:35:00Z",
  "updated_at": "2024-01-15T10:35:00Z"
}
```

#### Bulk Export Workflows
```http
POST /workflows/bulk-export
```

Export multiple workflows as a single ZIP archive.

**Example Request**:
```bash
curl -X POST "http://localhost:8000/workflows/bulk-export" \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -H "Accept: application/zip" \
  -d '{"workflow_ids": [123, 456, 789], "format": "zip"}' \
  -o bulk_exported_workflows.zip
```

## File Formats

### JSON Format

The JSON format includes:
- **version**: Export format version
- **exported_at**: Export timestamp
- **workflow**: Complete workflow data (nodes, edges, metadata)
- **metadata**: Export metadata (exporter, owner information)

### ZIP Format

ZIP archives contain:
- `workflow_[name].json`: Main workflow JSON file
- `README.md`: Import instructions and metadata
- `manifest.json`: Bulk export manifest (for bulk exports)

## Authentication

All endpoints require Bearer token authentication:

```http
Authorization: Bearer <your_access_token>
```

### Obtaining Tokens

1. **Login**: `POST /auth/login`
2. **Register**: `POST /auth/register`

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

## Integration Examples

### JavaScript/Node.js

```javascript
const axios = require('axios');

const API_BASE_URL = 'http://localhost:8000';
const TOKEN = 'your_access_token_here';

// Export workflow
async function exportWorkflow(workflowId, format = 'json') {
  const response = await axios.get(
    `${API_BASE_URL}/workflows/${workflowId}/export`,
    {
      params: { format },
      headers: {
        'Authorization': `Bearer ${TOKEN}`,
        'Accept': format === 'zip' ? 'application/zip' : 'application/json'
      }
    }
  );
  
  return response.data;
}

// Import workflow
async function importWorkflow(file, options = {}) {
  const formData = new FormData();
  formData.append('file', file);
  
  if (options.name) formData.append('name', options.name);
  if (options.description) formData.append('description', options.description);
  if (options.make_public) formData.append('make_public', options.make_public);
  
  const response = await axios.post(
    `${API_BASE_URL}/workflows/import`,
    formData,
    {
      headers: {
        'Authorization': `Bearer ${TOKEN}`
      }
    }
  );
  
  return response.data;
}
```

### Python

```python
import requests

API_BASE_URL = "http://localhost:8000"
TOKEN = "your_access_token_here"

headers = {
    "Authorization": f"Bearer {TOKEN}"
}

def export_workflow(workflow_id, format="json"):
    url = f"{API_BASE_URL}/workflows/{workflow_id}/export"
    params = {"format": format}
    
    response = requests.get(url, params=params, headers=headers)
    response.raise_for_status()
    
    return response.json() if format == "json" else response.content

def import_workflow(file_path, name=None, description=None, make_public=False):
    url = f"{API_BASE_URL}/workflows/import"
    
    files = {"file": open(file_path, "rb")}
    data = {}
    
    if name: data["name"] = name
    if description: data["description"] = description
    if make_public: data["make_public"] = "true"
    
    response = requests.post(url, files=files, data=data, headers=headers)
    response.raise_for_status()
    
    return response.json()
```

## Plugin Development

The import/export API is designed to support plugin development. See `PLUGIN_DEVELOPMENT_GUIDE.md` for detailed information on:

- Creating backup plugins
- Building migration tools
- Developing template management systems
- Integrating with external services

## Testing

### Using the Test Workflow File

A test workflow file is available at `c:\Users\tushar\Desktop\workflown2n\test-workflow.json`:

```json
{
  "name": "Test Workflow",
  "description": "A simple test workflow for import functionality",
  "nodes": [
    {
      "id": "1",
      "type": "input",
      "data": { "label": "Input Data" },
      "position": { "x": 100, "y": 50 }
    },
    {
      "id": "2",
      "type": "process",
      "data": { "label": "Process Data" },
      "position": { "x": 300, "y": 50 }
    },
    {
      "id": "3",
      "type": "output",
      "data": { "label": "Output Result" },
      "position": { "x": 500, "y": 50 }
    }
  ],
  "edges": [
    {
      "id": "e1-2",
      "source": "1",
      "target": "2"
    },
    {
      "id": "e2-3",
      "source": "2",
      "target": "3"
    }
  ],
  "is_public": false
}
```

### Test Import Command

```bash
curl -X POST "http://localhost:8000/workflows/import" \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -F "file=@c:\\Users\\tushar\\Desktop\\workflown2n\\test-workflow.json" \
  -F "name=Imported Test Workflow" \
  -F "description=Test workflow imported via API"
```

## Version History

- **v1.0.0**: Initial release with import/export functionality
- **v1.0.1**: Added bulk export support
- **v1.0.2**: Enhanced error handling and validation

## Support

For API support and questions:

- **Documentation**: See `API_INTEGRATION_GUIDE.md` for detailed integration examples
- **Plugin Development**: See `PLUGIN_DEVELOPMENT_GUIDE.md` for plugin development
- **Issues**: Report issues on the project repository
- **Contact**: support@workflown2n.com

## Contributing

To contribute to the API specifications:

1. Fork the repository
2. Make your changes to the OpenAPI YAML file
3. Test your changes using Swagger Editor or similar tools
4. Submit a pull request with a detailed description

## License

This OpenAPI specification is licensed under the MIT License. See the main project repository for full license details.