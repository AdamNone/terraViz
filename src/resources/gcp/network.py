"""
Network Resource Labeler.

This module handles the label generation for Networking components:
- VPC Networks
- Subnetworks
- Firewall Rules
"""

from src.utils import get_resource_value, get_resource_name

def get_firewall_label(resource):
    """
    Generates a label for Firewall Rules showing allowed ports and source ranges.
    """
    name = get_resource_name(resource)
    
    # Extract allowed ports
    ports = []
    exprs = resource.get('expressions', {})
    if 'allow' in exprs:
        allow_blocks = exprs['allow']
        if isinstance(allow_blocks, list):
            for block in allow_blocks:
                if 'ports' in block and 'constant_value' in block['ports']:
                    ports.extend(block['ports']['constant_value'])
    
    # Extract Source IP Ranges
    source_ranges = []
    if 'source_ranges' in exprs:
            val = exprs['source_ranges'].get('constant_value')
            if isinstance(val, list):
                source_ranges = val

    label = f"FW: {name}"
    if ports:
        # Truncate if too many ports
        label += f"\nPorts: {', '.join(ports[:3])}"
        if len(ports) > 3: label += "..."
    
    if source_ranges:
            # Truncate if too many source ranges
            label += f"\nSrc: {', '.join(source_ranges[:2])}"
            if len(source_ranges) > 2: label += "..."

    return label

def get_network_label(resource):
    """Generates a simple label for VPCs."""
    return f"VPC: {get_resource_name(resource)}"

def get_subnetwork_label(resource):
    """
    Generates a label for Subnets showing CIDR range and region.
    """
    name = get_resource_name(resource)
    cidr = get_resource_value(resource, "ip_cidr_range", "")
    region = get_resource_value(resource, "region", "")
    
    label = name
    if cidr:
        label += f"\n{cidr}"
    if region:
        label += f"\n{region}"
    return label