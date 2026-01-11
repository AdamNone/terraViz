def get_resource_value(resource, key, default=None):
    """Helper to safely get values from expressions or standard keys."""
    # Try direct key first (e.g. for 'type', 'name' etc at top level)
    if key in resource:
        return resource[key]
        
    # Try expressions -> key -> constant_value
    exprs = resource.get('expressions', {})
    if key in exprs:
        if isinstance(exprs[key], dict) and 'constant_value' in exprs[key]:
            return exprs[key]['constant_value']
    
    return default

def get_resource_name(resource):
    # Name resolution logic
    name_val = resource.get('name')
    if 'expressions' in resource and 'name' in resource['expressions']:
        val = resource['expressions']['name']
        if isinstance(val, dict) and 'constant_value' in val:
            name_val = val['constant_value']
    return name_val
