"""
Storage Resource Labeler.

This module handles the label generation for Cloud Storage Buckets.
It extracts details like location and bucket access policy.
"""

from src.utils import get_resource_value, get_resource_name

def get_label(resource):
    """
    Generates a label for google_storage_bucket.

    Includes:
    - Name
    - Location (e.g., US)
    - Uniform Bucket Level Access status
    """
    name = get_resource_name(resource)
    location = get_resource_value(resource, "location", "")
    uniform_access = get_resource_value(resource, "uniform_bucket_level_access", None)
    
    label = f"{name}"
    if location:
        label += f"\nLocation: {location}"
    if uniform_access is True:
        label += "\nUniform Access: Enabled"
        
    return label