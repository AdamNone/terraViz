"""
Resource Labeler Lookup.

This module acts as a registry for custom resource labeling logic. 
While `mapper.py` handles the *visual icon* (the class), this module handles 
the *text label* (the string) that appears below the icon.

It maps Terraform resource types to specific functions in the `src.resources.gcp` 
package that know how to extract relevant details (like IP addresses, machine types, 
or regions) from the resource's JSON representation.
"""

from src.resources.gcp import compute, database, storage, network
from src.utils import get_resource_name

# Registry mapping resource types to their custom label generator functions
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
    Generates a descriptive label for a resource.

    It first checks if a specialized labeler function exists for the resource type.
    If so, it uses that function to generate a rich label (e.g., including IP or machine type).
    If not, it falls back to simply returning the resource's name.

    Args:
        resource (dict): The resource dictionary from the Terraform plan.

    Returns:
        str: The generated label string.
    """
    res_type = resource['type']
    
    if res_type in RESOURCE_LABELERS:
        return RESOURCE_LABELERS[res_type](resource)
    
    # Fallback: Just return the resource name
    return get_resource_name(resource)