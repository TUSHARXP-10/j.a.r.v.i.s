# Workflow Import/Export Feature

This document describes the new workflow import/export functionality that has been added to the WorkflowN2N application.

## Overview

The workflow import/export feature allows users to:
- **Export individual workflows** in JSON or ZIP format
- **Import workflows** from JSON files
- **Bulk export multiple workflows** at once
- **Preserve workflow metadata** including creation dates, versions, and author information

## Backend API Endpoints

### 1. Export Single Workflow
```
GET /workflows/{workflow_id}/export?format={json|zip}
```

**Parameters:**
- `workflow_id`: The ID of the workflow to export
- `format`: Export format (json or zip)

**Response:**
- JSON format: Returns the workflow data as JSON
- ZIP format: Returns a ZIP file containing the workflow JSON and metadata

### 2. Import Workflow
```
POST /workflows/import
```

**Request Body:**
- Multipart form data with `file` field containing the workflow JSON file
- Optional `overwrite` parameter (boolean)

**Response:**
```json
{
  "id": "workflow_id",
  "name": "Workflow Name",
  "message": "Workflow imported successfully"
}
```

### 3. Bulk Export Workflows
```
POST /workflows/bulk-export
```

**Request Body:**
```json
{
  "workflow_ids": ["id1", "id2", "id3"],
  "format": "json|zip"
}
```

**Response:**
- JSON format: Returns an array of workflow objects
- ZIP format: Returns a ZIP file containing multiple workflow files

## Frontend Components

### WorkflowImportExport Component

The main component that provides the UI for import/export functionality.

**Location:** `src/components/WorkflowImportExport.jsx`

**Features:**
- **Import Section**: File upload interface with drag-and-drop support
- **Export Options**: Buttons for JSON and ZIP export formats
- **Bulk Export Panel**: Multi-workflow selection and bulk operations
- **Error Handling**: User-friendly error messages and loading states

**Props:**
- `workflowId`: Current workflow ID (for single workflow export)
- `workflowName`: Current workflow name
- `nodes`: Current workflow nodes
- `edges`: Current workflow edges
- `onImport`: Callback function when workflow is imported
- `savedWorkflows`: List of available workflows for bulk export

### WorkflowAPI Service

**Location:** `src/WorkflowAPI.js`

Provides API methods for:
- `exportWorkflow(workflowId, format)`: Export single workflow
- `importWorkflow(file, overwrite)`: Import workflow from file
- `bulkExportWorkflows(workflowIds, format)`: Export multiple workflows
- `getAllWorkflows()`: Get list of all workflows
- `downloadFile(blob, filename)`: Helper for file downloads
- `generateFilename(workflowName, format)`: Generate export filenames

## Usage Instructions

### Exporting a Workflow

1. **Open a workflow** in the visual editor
2. **Locate the Import/Export section** below the toolbar
3. **Choose export format:**
   - Click "Export as JSON" for a JSON file
   - Click "Export as ZIP" for a compressed archive
4. **File will be downloaded** automatically with a timestamped filename

### Importing a Workflow

1. **Click on the import area** or drag and drop a JSON file
2. **Select the workflow file** from your computer
3. **Wait for import to complete** (loading indicator will show)
4. **Workflow will be loaded** into the visual editor

### Bulk Export

1. **Click "Bulk Export" button** to open the selection panel
2. **Select workflows** using the checkboxes
3. **Choose export format** (JSON or ZIP)
4. **Click "Export Selected"** to download the files

## File Formats

### JSON Format
```json
{
  "name": "Workflow Name",
  "description": "Workflow description",
  "nodes": [...],
  "edges": [...],
  "metadata": {
    "version": "1.0",
    "created_at": "2024-01-01T00:00:00Z",
    "author": "username"
  }
}
```

### ZIP Format
Contains:
- `workflow.json`: The workflow data
- `metadata.json`: Additional metadata and version information

## Security Considerations

- **Authentication Required**: All import/export operations require valid authentication
- **Permission Checks**: Users can only export workflows they own or have access to
- **File Validation**: Imported files are validated for correct format and structure
- **Size Limits**: File uploads are limited to prevent abuse

## Error Handling

The system handles various error scenarios:
- **Invalid file format**: Clear error messages for unsupported file types
- **Missing permissions**: Appropriate error responses for unauthorized access
- **Network issues**: Retry mechanisms and user feedback
- **File corruption**: Validation checks and error reporting

## Browser Compatibility

The import/export feature works in all modern browsers that support:
- File API (for file uploads)
- Blob API (for file downloads)
- Fetch API (for API calls)

## Future Enhancements

Potential improvements for the import/export system:
- **Version control**: Track workflow versions and changes
- **Import validation**: Enhanced validation with detailed error reporting
- **Export templates**: Pre-defined workflow templates
- **Cloud storage**: Integration with cloud storage providers
- **Batch operations**: Enhanced bulk operations with progress tracking