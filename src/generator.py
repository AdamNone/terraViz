from diagrams import Diagram, Cluster
from src.mapper import get_diagram_node
from src.resources.lookup import get_resource_label
import json
import re
import os

def create_diagram(plan_path, output_filename="gcp_infra_diagram", show=False, outformat="png", save_script=False):
    with open(plan_path, 'r') as f:
        plan = json.load(f)

    resources = plan.get('configuration', {}).get('root_module', {}).get('resources', [])
    
    nodes = {}  # address -> {diagram_class, label, parent_addr}
    clusters = {} # address -> {type: 'vpc'|'subnet', label: str}

    # 1. Identify Clusters (VPCs and Subnets)
    for res in resources:
        res_type = res['type']
        address = res['address']
        
        if res_type == 'google_compute_network':
            label = get_resource_label(res)
            clusters[address] = {'type': 'vpc', 'label': label}
        elif res_type == 'google_compute_subnetwork':
             label = get_resource_label(res)
             clusters[address] = {'type': 'subnet', 'label': label}

    # Helper to find parent: Prioritize Subnet over VPC
    def find_parent_cluster(res_expressions):
        found_parents = []
        
        def search_refs(expr_data):
            if isinstance(expr_data, dict):
                if 'references' in expr_data:
                    for ref in expr_data['references']:
                        for cluster_addr in clusters:
                            if ref == cluster_addr or ref.startswith(cluster_addr + "."):
                                found_parents.append(cluster_addr)
                for v in expr_data.values():
                    search_refs(v)
            elif isinstance(expr_data, list):
                for v in expr_data:
                    search_refs(v)

        search_refs(res_expressions)
        
        # Filter found parents
        subnets = [p for p in found_parents if clusters[p]['type'] == 'subnet']
        vpcs = [p for p in found_parents if clusters[p]['type'] == 'vpc']
        
        if subnets: return subnets[0] # Return first subnet found
        if vpcs: return vpcs[0] # Return first vpc found
        return None

    # 2. Identify Nodes (Resources) and Assign to Clusters
    for res in resources:
        res_type = res['type']
        address = res['address']
        
        # Skip cluster resources (networks/subnets) as nodes
        if res_type in ['google_compute_network', 'google_compute_subnetwork']:
            continue

        diagram_class = get_diagram_node(res_type)
        
        if diagram_class:
            # Find parent
            expressions = res.get('expressions', {})
            parent_addr = find_parent_cluster(expressions)
            label = get_resource_label(res)
            
            nodes[address] = {'diagram_class': diagram_class, 'label': label, 'parent_addr': parent_addr}

    # 3. Render Diagram
    node_instances = {} # address -> instantiated Diagram node object
    
    # Enhanced Graph Attributes
    graph_attr = {
        "fontsize": "25",
        "bgcolor": "white",
        "splines": "ortho",
        "nodesep": "0.8",
        "ranksep": "1.0",
    }

    with Diagram("Terraform Infrastructure", show=show, filename=output_filename, outformat=outformat, graph_attr=graph_attr, direction="LR"):
        
        # Recursive writer for clusters
        def render_cluster(cluster_addr):
            cluster_data = clusters[cluster_addr]
            with Cluster(cluster_data["label"]):
                # Instantiate nodes belonging to this cluster
                cluster_node_addrs = [addr for addr, node in nodes.items() if node['parent_addr'] == cluster_addr]
                for node_addr in cluster_node_addrs:
                    node_data = nodes[node_addr]
                    cls = node_data['diagram_class']
                    node_instances[node_addr] = cls(node_data['label'])
                
                # Render child clusters (Subnets inside VPCs)
                if cluster_data['type'] == 'vpc':
                     # Find subnets that reference this VPC
                     child_subnets = []
                     for sub_addr, sub in clusters.items():
                         if sub['type'] == 'subnet':
                             res = next(r for r in resources if r['address'] == sub_addr)
                             if find_parent_cluster(res.get('expressions', {})) == cluster_addr:
                                 child_subnets.append(sub_addr)
                     
                     for sub_addr in child_subnets:
                         render_cluster(sub_addr)

        # Top Level VPCs
        vpcs = [addr for addr, c in clusters.items() if c['type'] == 'vpc']
        for vpc_addr in vpcs:
            render_cluster(vpc_addr)
            
        # Global nodes (no parent)
        global_nodes = [addr for addr, node in nodes.items() if node['parent_addr'] is None]
        for node_addr in global_nodes:
            node_data = nodes[node_addr]
            cls = node_data['diagram_class']
            node_instances[node_addr] = cls(node_data['label'])
    
    print(f"Diagram created: {output_filename}.{outformat}")

    # 4. Generate Script (Optional)
    if save_script:
        def sanitize_var_name(address):
            clean = re.sub(r'[^a-zA-Z0-9_]', '_', address)
            if clean[0].isdigit(): clean = "_" + clean
            return clean

        lines = []
        
        # Imports
        imports = set()
        for node in nodes.values():
            cls = node['diagram_class']
            imports.add((cls.__module__, cls.__name__))
        
        sorted_imports = sorted(list(imports))
        lines.append("from diagrams import Diagram, Cluster")
        for module, cls_name in sorted_imports:
            lines.append(f"from {module} import {cls_name}")
        lines.append("")
        
        lines.append(f"graph_attr = {json.dumps(graph_attr, indent=4)}")
        lines.append("")
        
        script_out_name = os.path.basename(output_filename)
        
        lines.append(f'with Diagram("Terraform Infrastructure", show=False, filename="{script_out_name}", outformat="{outformat}", graph_attr=graph_attr, direction="LR"):')
        
        node_vars = {} # address -> var_name
        
        def render_cluster_script(cluster_addr, indent_level):
            indent = "    " * indent_level
            cluster_data = clusters[cluster_addr]
            label = cluster_data['label'].replace('"', '"')
            
            lines.append(f'{indent}with Cluster("{label}"):')
            
            # Nodes
            cluster_node_addrs = [addr for addr, node in nodes.items() if node['parent_addr'] == cluster_addr]
            for node_addr in cluster_node_addrs:
                node_data = nodes[node_addr]
                cls_name = node_data['diagram_class'].__name__
                node_label_repr = repr(node_data['label'])
                var_name = sanitize_var_name(node_addr)
                node_vars[node_addr] = var_name
                
                lines.append(f'{indent}    {var_name} = {cls_name}({node_label_repr})')
                
            # Child Clusters
            if cluster_data['type'] == 'vpc':
                 child_subnets = []
                 for sub_addr, sub in clusters.items():
                     if sub['type'] == 'subnet':
                         res = next(r for r in resources if r['address'] == sub_addr)
                         if find_parent_cluster(res.get('expressions', {})) == cluster_addr:
                             child_subnets.append(sub_addr)
                 
                 for sub_addr in child_subnets:
                     render_cluster_script(sub_addr, indent_level + 1)

        # Top Level VPCs
        for vpc_addr in vpcs:
            render_cluster_script(vpc_addr, 1)
            
        # Global nodes
        for node_addr in global_nodes:
            node_data = nodes[node_addr]
            cls_name = node_data['diagram_class'].__name__
            node_label_repr = repr(node_data['label'])
            var_name = sanitize_var_name(node_addr)
            node_vars[node_addr] = var_name
            lines.append(f'    {var_name} = {cls_name}({node_label_repr})')

        script_filename = output_filename + ".py"
        with open(script_filename, "w") as f:
            f.write("\n".join(lines))
        
        print(f"Script saved: {script_filename}")