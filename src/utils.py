"""
Utilities for Parsing Terraform JSON.

This module contains helper functions to extract specific values from the 
Terraform plan JSON structure. Terraform's JSON output for resources can be 
complex, sometimes storing values directly in top-level keys and other times 
nesting them within an 'expressions' dictionary depending on how they were 
defined in the .tf file (e.g., as variables or constants).
"""

def get_resource_value(resource, key, default=None):
    """
    Safely retrieves a value from a resource dictionary, handling both direct keys
    and Terraform 'expressions'.

    Args:
        resource (dict): The resource dictionary from the parsed JSON plan.
        key (str): The attribute name to look up (e.g., 'machine_type', 'zone').
        default (any, optional): Value to return if the key is not found. Defaults to None.

    Returns:
        any: The extracted value or the default.
    """
    # 0. Try resolved planned values first (if available)
    # This handles cases where variables have been resolved in the plan.
    if 'planned_values' in resource and key in resource['planned_values']:
        return resource['planned_values'][key]

    # 1. Try direct key access first
    # Some attributes (like 'type', 'name', 'provider') are usually at the top level.
    if key in resource:
        return resource[key]
        
    # 2. Try looking inside 'expressions'
    # Most configuration values defined in the HCL will be under 'expressions'.
    # Example: { "expressions": { "machine_type": { "constant_value": "e2-micro" } } }
    exprs = resource.get('expressions', {})
    if key in exprs:
        # We check for 'constant_value' which indicates a static string/number/bool
        if isinstance(exprs[key], dict) and 'constant_value' in exprs[key]:
            return exprs[key]['constant_value']
    
    return default

def get_resource_name(resource):
    """
    Determines the logical name of the resource.
    
    Priority:
    1. 'name' inside 'planned_values' (resolved service name).
    2. 'name' inside 'expressions' (if the name was defined via a variable/expression).
    3. 'name' at the top level (the standard resource name).

    Args:
        resource (dict): The resource dictionary.

    Returns:
        str: The resolved name of the resource.
    """
    # 0. Try resolved planned name first
    if 'planned_values' in resource and 'name' in resource['planned_values']:
        return resource['planned_values']['name']

    # Default to the top-level name
    name_val = resource.get('name')
    
    # Check if a more specific name expression exists
    # (Rare, but possible if the name is dynamic)
    if 'expressions' in resource and 'name' in resource['expressions']:
        val = resource['expressions']['name']
        if isinstance(val, dict) and 'constant_value' in val:
            name_val = val['constant_value']
            
    return name_val