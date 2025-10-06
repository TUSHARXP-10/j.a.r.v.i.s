from abc import ABC, abstractmethod
from typing import Dict, List, Any, Optional
import logging

logger = logging.getLogger(__name__)

class BaseNodePlugin(ABC):
    """Base class for all workflow node plugins"""
    
    plugin_id: str
    name: str
    description: str
    version: str = "1.0.0"
    author: str = ""
    
    def __init__(self):
        if not hasattr(self, 'plugin_id') or not self.plugin_id:
            raise ValueError("Plugin must have a plugin_id")
        if not hasattr(self, 'name') or not self.name:
            raise ValueError("Plugin must have a name")
        if not hasattr(self, 'description') or not self.description:
            raise ValueError("Plugin must have a description")
    
    @abstractmethod
    def execute(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """Execute the plugin with the given input data"""
        pass
    
    @abstractmethod
    def get_input_schema(self) -> Dict[str, Any]:
        """Return JSON schema for input validation"""
        pass
    
    @abstractmethod
    def get_output_schema(self) -> Dict[str, Any]:
        """Return JSON schema for output validation"""
        pass
    
    @abstractmethod
    def get_config_schema(self) -> Dict[str, Any]:
        """Return JSON schema for configuration UI"""
        pass
    
    def validate_input(self, input_data: Dict[str, Any]) -> bool:
        """Validate input data against the schema"""
        try:
            schema = self.get_input_schema()
            # Simple validation - in production, use jsonschema library
            if schema.get('type') == 'object' and 'properties' in schema:
                required_props = schema.get('required', [])
                for prop in required_props:
                    if prop not in input_data:
                        raise ValueError(f"Missing required property: {prop}")
            return True
        except Exception as e:
            logger.error(f"Input validation failed for {self.plugin_id}: {e}")
            return False
    
    def get_metadata(self) -> Dict[str, Any]:
        """Get plugin metadata"""
        return {
            'plugin_id': self.plugin_id,
            'name': self.name,
            'description': self.description,
            'version': self.version,
            'author': self.author,
            'input_schema': self.get_input_schema(),
            'output_schema': self.get_output_schema(),
            'config_schema': self.get_config_schema()
        }


class PluginManager:
    """Manages registration and execution of plugins"""
    
    def __init__(self):
        self.plugins: Dict[str, BaseNodePlugin] = {}
        self.logger = logging.getLogger(__name__)
    
    def register_plugin(self, plugin: BaseNodePlugin) -> None:
        """Register a plugin"""
        if not isinstance(plugin, BaseNodePlugin):
            raise ValueError("Plugin must be an instance of BaseNodePlugin")
        
        plugin_id = plugin.plugin_id
        if plugin_id in self.plugins:
            self.logger.warning(f"Plugin '{plugin_id}' is already registered. Overwriting...")
        
        self.plugins[plugin_id] = plugin
        self.logger.info(f"Plugin '{plugin_id}' registered successfully")
    
    def unregister_plugin(self, plugin_id: str) -> None:
        """Unregister a plugin"""
        if plugin_id in self.plugins:
            del self.plugins[plugin_id]
            self.logger.info(f"Plugin '{plugin_id}' unregistered successfully")
        else:
            self.logger.warning(f"Plugin '{plugin_id}' not found for unregistration")
    
    def execute(self, plugin_id: str, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """Execute a plugin with the given input data"""
        plugin = self.plugins.get(plugin_id)
        if not plugin:
            raise ValueError(f"Plugin '{plugin_id}' not found")
        
        # Validate input data
        if not plugin.validate_input(input_data):
            raise ValueError(f"Invalid input data for plugin '{plugin_id}'")
        
        try:
            self.logger.info(f"Executing plugin '{plugin_id}' with input: {input_data}")
            result = plugin.execute(input_data)
            self.logger.info(f"Plugin '{plugin_id}' executed successfully")
            return result
        except Exception as e:
            self.logger.error(f"Plugin execution failed for '{plugin_id}': {e}")
            raise RuntimeError(f"Plugin execution failed: {str(e)}")
    
    def get_plugin(self, plugin_id: str) -> Optional[BaseNodePlugin]:
        """Get a plugin by ID"""
        return self.plugins.get(plugin_id)
    
    def list_plugins(self) -> List[BaseNodePlugin]:
        """List all registered plugins"""
        return list(self.plugins.values())
    
    def get_plugin_metadata(self, plugin_id: str) -> Optional[Dict[str, Any]]:
        """Get metadata for a specific plugin"""
        plugin = self.plugins.get(plugin_id)
        return plugin.get_metadata() if plugin else None
    
    def get_all_plugin_metadata(self) -> List[Dict[str, Any]]:
        """Get metadata for all plugins"""
        return [plugin.get_metadata() for plugin in self.plugins.values()]


# Global plugin manager instance
plugin_manager = PluginManager()