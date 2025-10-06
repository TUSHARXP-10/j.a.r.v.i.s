import os
import importlib
import inspect
import logging
from typing import Dict, List, Type, Optional, Any
from pathlib import Path
from plugin_system import BaseNodePlugin, PluginManager

logger = logging.getLogger(__name__)


class WorkflowPluginManager(PluginManager):
    """Extended plugin manager with workflow-specific functionality"""
    
    def __init__(self):
        super().__init__()
        self.plugin_instances: Dict[str, BaseNodePlugin] = {}
        self.plugin_configs: Dict[str, Dict[str, Any]] = {}
        
    def load_plugins_from_directory(self, plugins_dir: str) -> int:
        """Load plugins from a directory"""
        loaded_count = 0
        plugins_path = Path(plugins_dir)
        
        if not plugins_path.exists():
            logger.warning(f"Plugins directory not found: {plugins_dir}")
            return 0
        
        # Add plugins directory to Python path if not already there
        if str(plugins_path) not in os.sys.path:
            os.sys.path.insert(0, str(plugins_path))
        
        # Find all Python files in the directory
        for plugin_file in plugins_path.glob("*.py"):
            if plugin_file.name.startswith("_"):
                continue  # Skip private files
                
            try:
                module_name = plugin_file.stem
                spec = importlib.util.spec_from_file_location(module_name, plugin_file)
                module = importlib.util.module_from_spec(spec)
                spec.loader.exec_module(module)
                
                # Find plugin classes in the module
                for name, obj in inspect.getmembers(module, inspect.isclass):
                    if (issubclass(obj, BaseNodePlugin) and 
                        obj is not BaseNodePlugin and 
                        not inspect.isabstract(obj)):
                        
                        # Create instance
                        plugin_instance = obj()
                        self.register_plugin(plugin_instance)
                        loaded_count += 1
                        logger.info(f"Loaded plugin: {plugin_instance.plugin_id}")
                        
            except Exception as e:
                logger.error(f"Failed to load plugin from {plugin_file}: {e}")
        
        return loaded_count
    
    def load_builtin_plugins(self):
        """Load built-in plugins"""
        try:
            from plugins import HttpRequestPlugin, FileOperationPlugin, DelayPlugin
            
            builtin_plugins = [
                HttpRequestPlugin(),
                FileOperationPlugin(),
                DelayPlugin()
            ]
            
            for plugin in builtin_plugins:
                self.register_plugin(plugin)
                logger.info(f"Loaded built-in plugin: {plugin.plugin_id}")
                
        except ImportError as e:
            logger.error(f"Failed to load built-in plugins: {e}")
    
    def get_plugin_instance(self, plugin_id: str) -> Optional[BaseNodePlugin]:
        """Get a plugin instance by ID"""
        return self.plugin_instances.get(plugin_id)
    
    def set_plugin_config(self, plugin_id: str, config: Dict[str, Any]):
        """Set configuration for a plugin"""
        self.plugin_configs[plugin_id] = config
    
    def get_plugin_config(self, plugin_id: str) -> Dict[str, Any]:
        """Get configuration for a plugin"""
        return self.plugin_configs.get(plugin_id, {})
    
    def execute_plugin(self, plugin_id: str, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """Execute a plugin with input data"""
        plugin = self.get_plugin_instance(plugin_id)
        if not plugin:
            return {
                'success': False,
                'error': f'Plugin not found: {plugin_id}'
            }
        
        try:
            # Merge plugin config with input data
            config = self.get_plugin_config(plugin_id)
            merged_input = {**config, **input_data}
            
            # Validate input against schema
            schema = plugin.get_input_schema()
            if schema:
                self._validate_input(merged_input, schema)
            
            # Execute plugin
            result = plugin.execute(merged_input)
            
            # Validate output against schema
            output_schema = plugin.get_output_schema()
            if output_schema:
                self._validate_output(result, output_schema)
            
            return result
            
        except Exception as e:
            logger.error(f"Plugin execution failed: {e}")
            return {
                'success': False,
                'error': str(e)
            }
    
    def _validate_input(self, input_data: Dict[str, Any], schema: Dict[str, Any]):
        """Validate input data against schema"""
        # Basic validation - can be enhanced with jsonschema library
        if 'required' in schema:
            for field in schema['required']:
                if field not in input_data:
                    raise ValueError(f"Required field missing: {field}")
        
        # Validate field types
        if 'properties' in schema:
            for field, field_schema in schema['properties'].items():
                if field in input_data:
                    self._validate_field_type(input_data[field], field_schema, field)
    
    def _validate_output(self, output_data: Dict[str, Any], schema: Dict[str, Any]):
        """Validate output data against schema"""
        # Basic output validation
        if 'properties' in schema:
            for field, field_schema in schema['properties'].items():
                if field in output_data:
                    self._validate_field_type(output_data[field], field_schema, field)
    
    def _validate_field_type(self, value: Any, field_schema: Dict[str, Any], field_name: str):
        """Validate field type against schema"""
        if 'type' in field_schema:
            expected_type = field_schema['type']
            
            if isinstance(expected_type, list):
                # Multiple allowed types
                if not any(self._check_type(value, t) for t in expected_type):
                    raise ValueError(f"Field {field_name} must be one of types: {expected_type}")
            else:
                # Single type
                if not self._check_type(value, expected_type):
                    raise ValueError(f"Field {field_name} must be of type: {expected_type}")
    
    def _check_type(self, value: Any, expected_type: str) -> bool:
        """Check if value matches expected type"""
        type_map = {
            'string': str,
            'integer': int,
            'number': (int, float),
            'boolean': bool,
            'object': dict,
            'array': list
        }
        
        if expected_type in type_map:
            return isinstance(value, type_map[expected_type])
        
        return True  # Unknown type, allow it
    
    def get_plugin_metadata(self, plugin_id: str) -> Optional[Dict[str, Any]]:
        """Get plugin metadata"""
        plugin = self.get_plugin_instance(plugin_id)
        if not plugin:
            return None
        
        return {
            'plugin_id': plugin.plugin_id,
            'name': plugin.name,
            'description': plugin.description,
            'version': plugin.version,
            'author': plugin.author,
            'input_schema': plugin.get_input_schema(),
            'output_schema': plugin.get_output_schema(),
            'config_schema': plugin.get_config_schema()
        }


# Global plugin manager instance
plugin_manager = WorkflowPluginManager()