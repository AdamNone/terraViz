from .gcp.compute import ComputeInstanceHandler
from .gcp.database import SQLDatabaseInstanceHandler
from .gcp.storage import StorageBucketHandler
from .gcp.network import FirewallHandler, NetworkHandler, SubnetworkHandler

# Import the original generic mapper for fallbacks
from src.mapper import get_diagram_node as get_generic_diagram_node
from src.resources.base import ResourceHandler

class GenericHandler(ResourceHandler):
    def __init__(self, resource, diagram_cls):
        super().__init__(resource)
        self._diagram_cls = diagram_cls
        
    @property
    def diagram_class(self):
        return self._diagram_cls
        
    def get_label(self):
        return self.name

RESOURCE_HANDLERS = {
    "google_compute_instance": ComputeInstanceHandler,
    "google_sql_database_instance": SQLDatabaseInstanceHandler,
    "google_storage_bucket": StorageBucketHandler,
    "google_compute_firewall": FirewallHandler,
    "google_compute_network": NetworkHandler,
    "google_compute_subnetwork": SubnetworkHandler,
}

def get_resource_handler(resource):
    """
    Factory function to get the appropriate handler for a resource.
    """
    res_type = resource['type']
    
    if res_type in RESOURCE_HANDLERS:
        return RESOURCE_HANDLERS[res_type](resource)
    
    # Fallback to generic mapper
    generic_cls = get_generic_diagram_node(res_type)
    if generic_cls:
        return GenericHandler(resource, generic_cls)
        
    return None
