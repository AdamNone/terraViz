from abc import ABC, abstractmethod

class ResourceHandler(ABC):
    def __init__(self, resource):
        """
        :param resource: The dictionary representation of the resource from tfplan (root_module.resources entry)
        """
        self.resource = resource

    def _get_val(self, key, default=None):
        """Helper to safely get values from expressions or standard keys."""
        # Try direct key first (e.g. for 'type', 'name' etc at top level)
        if key in self.resource:
            return self.resource[key]
            
        # Try expressions -> key -> constant_value
        exprs = self.resource.get('expressions', {})
        if key in exprs:
            if 'constant_value' in exprs[key]:
                return exprs[key]['constant_value']
        
        return default

    @property
    def name(self):
        # Name resolution logic
        name_val = self.resource['name']
        if 'expressions' in self.resource and 'name' in self.resource['expressions']:
            if 'constant_value' in self.resource['expressions']['name']:
                name_val = self.resource['expressions']['name']['constant_value']
        return name_val

    @abstractmethod
    def get_label(self):
        """Returns the string label for the diagram node."""
        pass

    @property
    @abstractmethod
    def diagram_class(self):
        """Returns the Diagrams class (e.g. ComputeEngine)."""
        pass
