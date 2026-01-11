"""
Database Resource Labeler.

This module handles the label generation for Cloud SQL instances.
It extracts details like database version, machine tier, and IP configuration.
"""

from src.utils import get_resource_value, get_resource_name

def get_label(resource):
    """
    Generates a detailed label for a google_sql_database_instance.

    Includes:
    - Name
    - Database Version (e.g., POSTGRES_14)
    - Tier (e.g., db-f1-micro)
    - IP Configuration (Public/Private)

    Args:
        resource (dict): The resource dictionary.

    Returns:
        str: The multiline label string.
    """
    name = get_resource_name(resource)
    db_version = get_resource_value(resource, "database_version", "")
    
    tier = ""
    ip_info = []
    
    exprs = resource.get('expressions', {})
    if 'settings' in exprs:
        settings_list = exprs['settings']
        if isinstance(settings_list, list) and len(settings_list) > 0:
            setting = settings_list[0]
            
            tier = setting.get('tier', {}).get('constant_value', "")
            
            # Check for IP configuration
            if 'ip_configuration' in setting:
                ip_configs = setting['ip_configuration']
                if isinstance(ip_configs, list) and len(ip_configs) > 0:
                    ip_config = ip_configs[0]
                    ipv4_enabled = ip_config.get('ipv4_enabled', {}).get('constant_value')
                    
                    if ipv4_enabled is True:
                            ip_info.append("Public IP: Enabled")
                            
                    if 'private_network' in ip_config:
                            ip_info.append("Private IP: Enabled")

    # Construct the final label
    label = f"{name}"
    if db_version:
        label += f"\n{db_version}"
    if tier:
        label += f"\n{tier}"
    if ip_info:
        label += "\n" + "\n".join(ip_info)
    return label