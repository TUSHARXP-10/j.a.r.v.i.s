import json
import asyncio
import os
import sqlite3
from typing import Dict, List, Any, Optional
from datetime import datetime
import httpx
import aiofiles
import aiofiles.os

class WorkflowRunner:
    def __init__(self):
        self.logs = []
        self.node_outputs = {}
        self.execution_order = []
        
    def log(self, message: str, level: str = "INFO"):
        """Add a log entry"""
        log_entry = {
            "timestamp": datetime.now().isoformat(),
            "level": level,
            "message": message
        }
        self.logs.append(log_entry)
        print(f"[{level}] {message}")
    
    def get_logs(self) -> List[Dict[str, Any]]:
        """Get all logs"""
        return self.logs
    
    def clear_logs(self):
        """Clear all logs"""
        self.logs = []
    
    def build_execution_graph(self, nodes: List[Dict], edges: List[Dict]) -> List[str]:
        """Build execution order based on node dependencies"""
        # Create adjacency list for graph
        graph = {}
        in_degree = {}
        
        # Initialize all nodes
        for node in nodes:
            node_id = node['id']
            graph[node_id] = []
            in_degree[node_id] = 0
        
        # Build graph and calculate in-degrees
        for edge in edges:
            source = edge['source']
            target = edge['target']
            if source in graph:
                graph[source].append(target)
                in_degree[target] += 1
        
        # Topological sort using Kahn's algorithm
        queue = [node_id for node_id in in_degree if in_degree[node_id] == 0]
        execution_order = []
        
        while queue:
            current = queue.pop(0)
            execution_order.append(current)
            
            for neighbor in graph[current]:
                in_degree[neighbor] -= 1
                if in_degree[neighbor] == 0:
                    queue.append(neighbor)
        
        # Check for cycles
        if len(execution_order) != len(nodes):
            raise ValueError("Workflow contains cycles and cannot be executed")
        
        return execution_order
    
    async def execute_node(self, node: Dict, input_data: Dict) -> Any:
        """Execute a single node based on its type"""
        node_id = node['id']
        node_type = node['type']
        node_config = node.get('data', {}).get('config', {})
        
        self.log(f"Executing node {node_id} of type {node_type}")
        
        try:
            if node_type == "input":
                # Input node - return input data or config value
                result = input_data.get('value', node_config.get('value', ''))
                self.log(f"Input node returned: {result}")
                return result
            
            elif node_type == "plugin":
                # Plugin node - execute plugin with configuration
                plugin_id = node.get('data', {}).get('pluginId')
                plugin_config = node.get('data', {}).get('config', {})
                
                if not plugin_id:
                    self.log(f"Plugin ID not specified for node {node_id}", "ERROR")
                    raise ValueError(f"Plugin ID not specified for node {node_id}")
                
                # Execute plugin through plugin manager
                from main import plugin_manager
                result = await plugin_manager.execute_plugin(plugin_id, input_data, plugin_config)
                self.log(f"Plugin node {plugin_id} returned: {result}")
                return result
            
            elif node_type == "action":
                # Action node - perform configured action
                action_type = node_config.get('actionType', 'log')
                action_config = node_config.get('actionConfig', {})
                
                if action_type == "log":
                    message = action_config.get('message', 'No message provided')
                    self.log(f"Log action: {message}")
                    return message
                
                elif action_type == "http_request":
                    return await self.execute_http_request(action_config)
                
                elif action_type == "transform":
                    return self.execute_transform(input_data, action_config)
                
                elif action_type == "file_operation":
                    return await self.execute_file_operation(action_config)
                
                elif action_type == "database":
                    return await self.execute_database_operation(action_config)
                
                elif action_type == "condition":
                    return self.execute_condition(input_data, action_config)
                
                elif action_type == "delay":
                    return await self.execute_delay(action_config)
                
                else:
                    self.log(f"Unknown action type: {action_type}", "WARNING")
                    return None
            
            elif node_type == "output":
                # Output node - format and return final output
                output_format = node_config.get('format', 'raw')
                output_value = input_data.get('value', '')
                
                if output_format == 'json':
                    result = json.dumps(output_value, indent=2)
                elif output_format == 'table':
                    result = self.format_as_table(output_value)
                else:
                    result = str(output_value)
                
                self.log(f"Output node formatted result: {result}")
                return result
            
            else:
                self.log(f"Unknown node type: {node_type}", "WARNING")
                return None
                
        except Exception as e:
            self.log(f"Error executing node {node_id}: {str(e)}", "ERROR")
            raise
    
    async def execute_http_request(self, config: Dict) -> Dict[str, Any]:
        """Execute HTTP request"""
        method = config.get('method', 'GET').upper()
        url = config.get('url', '')
        headers = config.get('headers', {})
        body = config.get('body', '')
        
        if not url:
            raise ValueError("URL is required for HTTP request")
        
        self.log(f"Making {method} request to {url}")
        
        async with httpx.AsyncClient() as client:
            if method == 'GET':
                response = await client.get(url, headers=headers)
            elif method == 'POST':
                response = await client.post(url, headers=headers, json=body)
            elif method == 'PUT':
                response = await client.put(url, headers=headers, json=body)
            elif method == 'DELETE':
                response = await client.delete(url, headers=headers)
            else:
                raise ValueError(f"Unsupported HTTP method: {method}")
            
            result = {
                "status_code": response.status_code,
                "headers": dict(response.headers),
                "body": response.text,
                "json": response.json() if response.headers.get('content-type', '').startswith('application/json') else None
            }
            
            self.log(f"HTTP request completed with status {response.status_code}")
            return result
    
    def execute_transform(self, input_data: Dict, config: Dict) -> Any:
        """Execute data transformation"""
        transform_type = config.get('transformType', 'uppercase')
        input_key = config.get('inputKey', 'value')
        
        input_value = input_data.get(input_key, '')
        
        if transform_type == 'uppercase':
            result = str(input_value).upper()
        elif transform_type == 'lowercase':
            result = str(input_value).lower()
        elif transform_type == 'reverse':
            result = str(input_value)[::-1]
        elif transform_type == 'length':
            result = len(str(input_value))
        else:
            result = input_value
        
        self.log(f"Transform {transform_type} applied, result: {result}")
        return result
    
    async def execute_file_operation(self, config: Dict) -> Any:
        """Execute file operations"""
        operation = config.get('operation', 'read')
        file_path = config.get('filePath', '')
        content = config.get('content', '')
        
        if not file_path:
            raise ValueError("File path is required for file operations")
        
        try:
            if operation == 'read':
                async with aiofiles.open(file_path, 'r') as file:
                    content = await file.read()
                self.log(f"File read from {file_path}")
                return content
            
            elif operation == 'write':
                async with aiofiles.open(file_path, 'w') as file:
                    await file.write(content)
                self.log(f"File written to {file_path}")
                return f"File written successfully to {file_path}"
            
            elif operation == 'append':
                async with aiofiles.open(file_path, 'a') as file:
                    await file.write(content)
                self.log(f"Content appended to {file_path}")
                return f"Content appended successfully to {file_path}"
            
            elif operation == 'exists':
                exists = os.path.exists(file_path)
                self.log(f"File existence check for {file_path}: {exists}")
                return exists
            
            else:
                raise ValueError(f"Unknown file operation: {operation}")
                
        except Exception as e:
            self.log(f"File operation failed: {str(e)}", "ERROR")
            raise
    
    async def execute_database_operation(self, config: Dict) -> Any:
        """Execute database operations (simplified SQLite implementation)"""
        operation = config.get('operation', 'query')
        database_path = config.get('databasePath', 'data/workflow_data.db')
        query = config.get('query', '')
        params = config.get('params', [])
        
        if not query:
            raise ValueError("Query is required for database operations")
        
        try:
            # Ensure data directory exists
            os.makedirs(os.path.dirname(database_path), exist_ok=True)
            
            conn = sqlite3.connect(database_path)
            cursor = conn.cursor()
            
            if operation == 'query':
                cursor.execute(query, params)
                results = cursor.fetchall()
                conn.close()
                
                # Convert to list of dicts for JSON serialization
                if cursor.description:
                    columns = [desc[0] for desc in cursor.description]
                    results = [dict(zip(columns, row)) for row in results]
                
                self.log(f"Database query executed, returned {len(results)} rows")
                return results
            
            elif operation == 'execute':
                cursor.execute(query, params)
                conn.commit()
                rowcount = cursor.rowcount
                conn.close()
                
                self.log(f"Database execute completed, affected {rowcount} rows")
                return f"Query executed successfully, affected {rowcount} rows"
            
            else:
                conn.close()
                raise ValueError(f"Unknown database operation: {operation}")
                
        except Exception as e:
            self.log(f"Database operation failed: {str(e)}", "ERROR")
            raise
    
    def execute_condition(self, input_data: Dict, config: Dict) -> Any:
        """Execute conditional logic"""
        condition_type = config.get('conditionType', 'equals')
        input_key = config.get('inputKey', 'value')
        expected_value = config.get('expectedValue', '')
        true_value = config.get('trueValue', 'true')
        false_value = config.get('falseValue', 'false')
        
        input_value = input_data.get(input_key, '')
        
        if condition_type == 'equals':
            result = true_value if str(input_value) == str(expected_value) else false_value
        elif condition_type == 'not_equals':
            result = true_value if str(input_value) != str(expected_value) else false_value
        elif condition_type == 'contains':
            result = true_value if str(expected_value) in str(input_value) else false_value
        elif condition_type == 'greater_than':
            try:
                result = true_value if float(input_value) > float(expected_value) else false_value
            except (ValueError, TypeError):
                result = false_value
        elif condition_type == 'less_than':
            try:
                result = true_value if float(input_value) < float(expected_value) else false_value
            except (ValueError, TypeError):
                result = false_value
        else:
            result = false_value
        
        self.log(f"Condition {condition_type} evaluated: {input_value} -> {result}")
        return result
    
    async def execute_delay(self, config: Dict) -> str:
        """Execute delay/wait"""
        delay_seconds = config.get('delaySeconds', 1)
        
        self.log(f"Starting delay for {delay_seconds} seconds")
        await asyncio.sleep(delay_seconds)
        self.log(f"Delay completed after {delay_seconds} seconds")
        
        return f"Delayed for {delay_seconds} seconds"
    
    def format_as_table(self, data: Any) -> str:
        """Format data as a simple table"""
        if isinstance(data, list) and len(data) > 0 and isinstance(data[0], dict):
            # List of dictionaries - create table
            headers = list(data[0].keys())
            rows = [[str(row.get(header, '')) for header in headers] for row in data]
            
            # Simple table formatting
            table = " | ".join(headers) + "\n"
            table += "-" * len(table) + "\n"
            for row in rows:
                table += " | ".join(row) + "\n"
            
            return table
        else:
            return str(data)
    
    def get_node_inputs(self, node_id: str, edges: List[Dict]) -> Dict[str, Any]:
        """Get input data for a node from connected nodes"""
        inputs = {}
        
        # Find all edges that connect to this node
        for edge in edges:
            if edge['target'] == node_id:
                source_node_id = edge['source']
                if source_node_id in self.node_outputs:
                    # Use the output from the source node
                    inputs.update(self.node_outputs[source_node_id])
        
        return inputs
    
    async def execute_workflow(self, nodes: List[Dict], edges: List[Dict], input_data: Dict = None) -> Dict[str, Any]:
        """Execute the entire workflow"""
        self.clear_logs()
        self.node_outputs = {}
        
        if input_data is None:
            input_data = {}
        
        self.log("Starting workflow execution")
        
        try:
            # Build execution order
            execution_order = self.build_execution_graph(nodes, edges)
            self.log(f"Execution order: {execution_order}")
            
            # Create node lookup
            node_lookup = {node['id']: node for node in nodes}
            
            # Execute nodes in order
            for node_id in execution_order:
                node = node_lookup[node_id]
                
                # Get input data for this node
                node_inputs = self.get_node_inputs(node_id, edges)
                
                # If no inputs from other nodes, use the global input data
                if not node_inputs:
                    node_inputs = input_data.copy()
                
                # Execute the node
                result = await self.execute_node(node, node_inputs)
                
                # Store the output
                self.node_outputs[node_id] = {"value": result}
            
            # Get final output (from the last executed node)
            final_output = self.node_outputs.get(execution_order[-1], {}).get('value', None)
            
            self.log("Workflow execution completed successfully")
            
            return {
                "status": "success",
                "output": final_output,
                "node_outputs": self.node_outputs,
                "execution_order": execution_order
            }
            
        except Exception as e:
            self.log(f"Workflow execution failed: {str(e)}", "ERROR")
            return {
                "status": "failed",
                "error": str(e),
                "node_outputs": self.node_outputs
            }