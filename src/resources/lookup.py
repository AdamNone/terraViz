from src.resources.gcp import compute, database, storage, network
from src.utils import get_resource_name

RESOURCE_LABELERS = {
    "google_compute_instance": compute.get_label,
    "google_sql_database_instance": database.get_label,
    "google_storage_bucket": storage.get_label,
    "google_compute_firewall": network.get_firewall_label,
    "google_compute_network": network.get_network_label,
    "google_compute_subnetwork": network.get_subnetwork_label,
}

def get_resource_label(resource):
    """
    Returns the label for a resource using a specific labeler if available,
    otherwise defaults to the resource name.
    """
    res_type = resource['type']
    if res_type in RESOURCE_LABELERS:
        return RESOURCE_LABELERS[res_type](resource)
    
    return get_resource_name(resource)
