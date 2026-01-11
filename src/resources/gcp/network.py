from src.utils import get_resource_value, get_resource_name

def get_firewall_label(resource):
    name = get_resource_name(resource)
    # Extract ports
    ports = []
    exprs = resource.get('expressions', {})
    if 'allow' in exprs:
        allow_blocks = exprs['allow']
        if isinstance(allow_blocks, list):
            for block in allow_blocks:
                if 'ports' in block and 'constant_value' in block['ports']:
                    ports.extend(block['ports']['constant_value'])
    
    # Extract Source Ranges
    source_ranges = []
    if 'source_ranges' in exprs:
            val = exprs['source_ranges'].get('constant_value')
            if isinstance(val, list):
                source_ranges = val

    label = f"FW: {name}"
    if ports:
        label += f"\nPorts: {', '.join(ports[:3])}"
        if len(ports) > 3: label += "..."
    
    if source_ranges:
            label += f"\nSrc: {', '.join(source_ranges[:2])}"
            if len(source_ranges) > 2: label += "..."

    return label

def get_network_label(resource):
    return f"VPC: {get_resource_name(resource)}"

def get_subnetwork_label(resource):
    name = get_resource_name(resource)
    cidr = get_resource_value(resource, "ip_cidr_range", "")
    region = get_resource_value(resource, "region", "")
    
    label = name
    if cidr:
        label += f"\n{cidr}"
    if region:
        label += f"\n{region}"
    return label
