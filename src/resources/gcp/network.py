from ..base import ResourceHandler
from diagrams.gcp.network import FirewallRules, VirtualPrivateCloud, Router

class FirewallHandler(ResourceHandler):
    @property
    def diagram_class(self):
        return FirewallRules

    def get_label(self):
        name = self.name
        # Extract ports
        ports = []
        exprs = self.resource.get('expressions', {})
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

class NetworkHandler(ResourceHandler):
    @property
    def diagram_class(self):
        return VirtualPrivateCloud

    def get_label(self):
        return f"VPC: {self.name}"

class SubnetworkHandler(ResourceHandler):
    @property
    def diagram_class(self):
        return Router 

    def get_label(self):
        name = self.name
        cidr = self._get_val("ip_cidr_range", "")
        region = self._get_val("region", "")
        
        label = name
        if cidr:
            label += f"\n{cidr}"
        if region:
            label += f"\n{region}"
        return label