import requests
import json
import logging
from typing import Dict, Any
from plugin_system import BaseNodePlugin

logger = logging.getLogger(__name__)


class HttpRequestPlugin(BaseNodePlugin):
    """HTTP Request Plugin - Performs HTTP requests"""
    
    plugin_id = "http_request"
    name = "HTTP Request"
    description = "Performs HTTP GET, POST, PUT, DELETE requests"
    version = "1.0.0"
    author = "WorkflowN2N Team"
    
    def execute(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """Execute HTTP request"""
        try:
            method = input_data.get('method', 'GET').upper()
            url = input_data.get('url', '')
            headers = input_data.get('headers', {})
            body = input_data.get('body', '')
            timeout = input_data.get('timeout', 30)
            
            if not url:
                raise ValueError("URL is required")
            
            # Parse body if it's JSON
            if body and isinstance(body, str):
                try:
                    body = json.loads(body)
                except json.JSONDecodeError:
                    pass  # Keep as string if not valid JSON
            
            # Prepare request parameters
            request_params = {
                'url': url,
                'headers': headers,
                'timeout': timeout
            }
            
            # Add body for POST, PUT, PATCH requests
            if method in ['POST', 'PUT', 'PATCH'] and body:
                if isinstance(body, dict):
                    request_params['json'] = body
                else:
                    request_params['data'] = body
            
            # Execute request
            response = requests.request(method, **request_params)
            
            # Prepare response data
            response_data = {
                'status_code': response.status_code,
                'headers': dict(response.headers),
                'body': response.text,
                'success': response.status_code < 400
            }
            
            # Try to parse JSON response
            try:
                response_data['json'] = response.json()
            except json.JSONDecodeError:
                response_data['json'] = None
            
            return response_data
            
        except Exception as e:
            logger.error(f"HTTP request failed: {e}")
            return {
                'success': False,
                'error': str(e),
                'status_code': None,
                'body': None,
                'headers': {}
            }
    
    def get_input_schema(self) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "method": {
                    "type": "string",
                    "enum": ["GET", "POST", "PUT", "DELETE", "PATCH"],
                    "default": "GET",
                    "description": "HTTP method"
                },
                "url": {
                    "type": "string",
                    "description": "Target URL for the request"
                },
                "headers": {
                    "type": "object",
                    "description": "HTTP headers as key-value pairs",
                    "default": {}
                },
                "body": {
                    "type": ["string", "object"],
                    "description": "Request body (for POST, PUT, PATCH)",
                    "default": ""
                },
                "timeout": {
                    "type": "integer",
                    "description": "Request timeout in seconds",
                    "default": 30,
                    "minimum": 1,
                    "maximum": 300
                }
            },
            "required": ["url"]
        }
    
    def get_output_schema(self) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "success": {
                    "type": "boolean",
                    "description": "Whether the request was successful"
                },
                "status_code": {
                    "type": ["integer", "null"],
                    "description": "HTTP status code"
                },
                "headers": {
                    "type": "object",
                    "description": "Response headers"
                },
                "body": {
                    "type": ["string", "null"],
                    "description": "Response body as text"
                },
                "json": {
                    "type": ["object", "array", "null"],
                    "description": "Parsed JSON response if available"
                },
                "error": {
                    "type": ["string", "null"],
                    "description": "Error message if request failed"
                }
            }
        }
    
    def get_config_schema(self) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "default_timeout": {
                    "type": "integer",
                    "description": "Default timeout for requests",
                    "default": 30
                },
                "max_redirects": {
                    "type": "integer",
                    "description": "Maximum number of redirects to follow",
                    "default": 5
                }
            }
        }


class FileOperationPlugin(BaseNodePlugin):
    """File Operation Plugin - Read/Write files"""
    
    plugin_id = "file_operation"
    name = "File Operation"
    description = "Read from and write to files"
    version = "1.0.0"
    author = "WorkflowN2N Team"
    
    def execute(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """Execute file operation"""
        try:
            operation = input_data.get('operation', 'read')
            file_path = input_data.get('file_path', '')
            content = input_data.get('content', '')
            encoding = input_data.get('encoding', 'utf-8')
            
            if not file_path:
                raise ValueError("File path is required")
            
            if operation == 'read':
                try:
                    with open(file_path, 'r', encoding=encoding) as file:
                        content = file.read()
                    return {
                        'success': True,
                        'content': content,
                        'operation': 'read',
                        'file_path': file_path
                    }
                except FileNotFoundError:
                    return {
                        'success': False,
                        'error': f"File not found: {file_path}",
                        'operation': 'read',
                        'file_path': file_path
                    }
                except UnicodeDecodeError:
                    return {
                        'success': False,
                        'error': f"Cannot decode file with encoding: {encoding}",
                        'operation': 'read',
                        'file_path': file_path
                    }
            
            elif operation == 'write':
                try:
                    with open(file_path, 'w', encoding=encoding) as file:
                        file.write(content)
                    return {
                        'success': True,
                        'operation': 'write',
                        'file_path': file_path,
                        'bytes_written': len(content.encode(encoding))
                    }
                except PermissionError:
                    return {
                        'success': False,
                        'error': f"Permission denied: {file_path}",
                        'operation': 'write',
                        'file_path': file_path
                    }
            
            else:
                raise ValueError(f"Unsupported operation: {operation}")
                
        except Exception as e:
            logger.error(f"File operation failed: {e}")
            return {
                'success': False,
                'error': str(e),
                'operation': operation,
                'file_path': file_path
            }
    
    def get_input_schema(self) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "operation": {
                    "type": "string",
                    "enum": ["read", "write"],
                    "description": "File operation to perform"
                },
                "file_path": {
                    "type": "string",
                    "description": "Path to the file"
                },
                "content": {
                    "type": "string",
                    "description": "Content to write (for write operation)",
                    "default": ""
                },
                "encoding": {
                    "type": "string",
                    "description": "File encoding",
                    "default": "utf-8",
                    "enum": ["utf-8", "utf-16", "ascii", "latin-1"]
                }
            },
            "required": ["operation", "file_path"]
        }
    
    def get_output_schema(self) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "success": {
                    "type": "boolean",
                    "description": "Whether the operation was successful"
                },
                "operation": {
                    "type": "string",
                    "enum": ["read", "write"],
                    "description": "The operation that was performed"
                },
                "file_path": {
                    "type": "string",
                    "description": "Path to the file"
                },
                "content": {
                    "type": ["string", "null"],
                    "description": "File content (for read operation)"
                },
                "bytes_written": {
                    "type": ["integer", "null"],
                    "description": "Number of bytes written (for write operation)"
                },
                "error": {
                    "type": ["string", "null"],
                    "description": "Error message if operation failed"
                }
            }
        }
    
    def get_config_schema(self) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "max_file_size": {
                    "type": "integer",
                    "description": "Maximum file size in bytes",
                    "default": 10485760  # 10MB
                },
                "allowed_extensions": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "Allowed file extensions",
                    "default": [".txt", ".json", ".csv", ".xml", ".yaml", ".yml"]
                }
            }
        }


class DelayPlugin(BaseNodePlugin):
    """Delay Plugin - Add delays to workflow execution"""
    
    plugin_id = "delay"
    name = "Delay"
    description = "Add a delay to workflow execution"
    version = "1.0.0"
    author = "WorkflowN2N Team"
    
    def execute(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """Execute delay"""
        import time
        
        try:
            delay_seconds = input_data.get('delay_seconds', 1)
            
            if delay_seconds < 0:
                raise ValueError("Delay seconds must be non-negative")
            
            # Add delay
            time.sleep(delay_seconds)
            
            return {
                'success': True,
                'delay_seconds': delay_seconds,
                'message': f'Delayed for {delay_seconds} seconds'
            }
            
        except Exception as e:
            logger.error(f"Delay operation failed: {e}")
            return {
                'success': False,
                'error': str(e),
                'delay_seconds': delay_seconds if 'delay_seconds' in locals() else None
            }
    
    def get_input_schema(self) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "delay_seconds": {
                    "type": "number",
                    "description": "Number of seconds to delay",
                    "default": 1,
                    "minimum": 0,
                    "maximum": 3600  # 1 hour max
                }
            },
            "required": ["delay_seconds"]
        }
    
    def get_output_schema(self) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "success": {
                    "type": "boolean",
                    "description": "Whether the delay was successful"
                },
                "delay_seconds": {
                    "type": "number",
                    "description": "Number of seconds delayed"
                },
                "message": {
                    "type": ["string", "null"],
                    "description": "Success message"
                },
                "error": {
                    "type": ["string", "null"],
                    "description": "Error message if delay failed"
                }
            }
        }
    
    def get_config_schema(self) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "max_delay": {
                    "type": "number",
                    "description": "Maximum allowed delay in seconds",
                    "default": 3600
                }
            }
        }