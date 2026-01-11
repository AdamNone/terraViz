"""
Core Diagram Generator.

This module contains the main logic for parsing the Terraform plan and 
rendering the architecture diagram. It uses the `diagrams` library to 
create the visual output.

The process involves:
1. Parsing the JSON plan.
2. Identifying "container" resources (VPCs, Subnets) which act as Clusters.
3. Identifying standard resources (Compute, DB, etc.) which act as Nodes.
4. Resolving relationships (which resource belongs to which subnet/VPC).
5. Rendering the diagram.
6. Optionally generating a Python script that can reproduce the diagram.
"""

from diagrams import Diagram, Cluster
from src.mapper import get_diagram_node
from src.resources.lookup import get_resource_label
import json
import re
import os

def create_diagram(plan_path, output_filename="gcp_infra_diagram", show=False, outformat="png", save_script=False):
    """
    Parses a Terraform plan and generates an infrastructure diagram.

    Args:
        plan_path (str): Path to the tfplan.json file.
        output_filename (str, optional): Base filename for the output (no extension). Defaults to "gcp_infra_diagram".
        show (bool, optional): Whether to open the image after generation. Defaults to False.
        outformat (str, optional): Output image format (png, jpg, dot). Defaults to "png".
        save_script (bool, optional): If True, saves the Python code used to generate the diagram. Defaults to False.
    """
    
    # Load the JSON plan
    with open(plan_path, 'r') as f:
        plan = json.load(f)

    # Extract the list of resources from the root module
    resources = plan.get('configuration', {}).get('root_module', {}).get('resources', [])
    
    nodes = {}  # Map: resource_address -> {diagram_class, label, parent_addr}
    clusters = {} # Map: resource_address -> {type: 'vpc'|'subnet', label: str}

    # =========================================================================
    # Step 1: Identify Clusters (VPCs and Subnets)
    # =========================================================================
    # We identify network containers first so we can later check if other resources
    # belong to them.
    for res in resources:
        res_type = res['type']
        address = res['address']
        
        if res_type == 'google_compute_network':
            label = get_resource_label(res)
            clusters[address] = {'type': 'vpc', 'label': label}
        elif res_type == 'google_compute_subnetwork':
             label = get_resource_label(res)
             clusters[address] = {'type': 'subnet', 'label': label}

    # Helper function to resolve parent relationships
    def find_parent_cluster(res_expressions):
        """
        Recursively searches resource expressions for references to known clusters (VPCs/Subnets).
        Prioritizes Subnets over VPCs (deepest nesting).
        """
        found_parents = []
        
        def search_refs(expr_data):
            if isinstance(expr_data, dict):
                # 'references' key contains list of resource addresses this block refers to
                if 'references' in expr_data:
                    for ref in expr_data['references']:
                        for cluster_addr in clusters:
                            # Match exact address or sub-attribute (e.g., module.vpc.network_id)
                            if ref == cluster_addr or ref.startswith(cluster_addr + "."):
                                found_parents.append(cluster_addr)
                # Recursively search nested dictionaries
                for v in expr_data.values():
                    search_refs(v)
            elif isinstance(expr_data, list):
                # Recursively search lists
                for v in expr_data:
                    search_refs(v)

        search_refs(res_expressions)
        
        # Categorize found parents
        subnets = [p for p in found_parents if clusters[p]['type'] == 'subnet']
        vpcs = [p for p in found_parents if clusters[p]['type'] == 'vpc']
        
        # Return the most specific parent (Subnet > VPC)
        if subnets: return subnets[0] 
        if vpcs: return vpcs[0] 
        return None

    # =========================================================================
    # Step 2: Identify Nodes (Resources) and Assign to Clusters
    # =========================================================================
    for res in resources:
        res_type = res['type']
        address = res['address']
        
        # Skip resources that are themselves clusters (we handled them in Step 1)
        if res_type in ['google_compute_network', 'google_compute_subnetwork']:
            continue

        # Get the corresponding Diagrams class (visual icon)
        diagram_class = get_diagram_node(res_type)
        
        if diagram_class:
            # Determine which cluster (if any) this resource belongs to
            expressions = res.get('expressions', {})
            parent_addr = find_parent_cluster(expressions)
            
            # Generate the text label
            label = get_resource_label(res)
            
            nodes[address] = {'diagram_class': diagram_class, 'label': label, 'parent_addr': parent_addr}

    # =========================================================================
    # Step 3: Render Diagram
    # =========================================================================
    node_instances = {} # Map: address -> instantiated Diagram node object
    
    # Graphviz global attributes for styling
    graph_attr = {
        "fontsize": "25",
        "bgcolor": "white",
        "splines": "ortho", # Orthogonal lines for cleaner look
        "nodesep": "0.8",   # Horizontal separation
        "ranksep": "1.0",   # Vertical separation
    }

    with Diagram("Terraform Infrastructure", show=show, filename=output_filename, outformat=outformat, graph_attr=graph_attr, direction="LR"):
        
        # Recursive function to render clusters and their contents
        def render_cluster(cluster_addr):
            cluster_data = clusters[cluster_addr]
            
            with Cluster(cluster_data["label"]):
                # 1. Instantiate nodes belonging directly to this cluster
                cluster_node_addrs = [addr for addr, node in nodes.items() if node['parent_addr'] == cluster_addr]
                for node_addr in cluster_node_addrs:
                    node_data = nodes[node_addr]
                    cls = node_data['diagram_class']
                    node_instances[node_addr] = cls(node_data['label'])
                
                # 2. Recursively render child clusters (e.g., Subnets inside this VPC)
                if cluster_data['type'] == 'vpc':
                     # Find subnets that reference this specific VPC
                     child_subnets = []
                     for sub_addr, sub in clusters.items():
                         if sub['type'] == 'subnet':
                             # We need to look up the subnet resource again to find its references
                             res = next(r for r in resources if r['address'] == sub_addr)
                             if find_parent_cluster(res.get('expressions', {})) == cluster_addr:
                                 child_subnets.append(sub_addr)
                     
                     for sub_addr in child_subnets:
                         render_cluster(sub_addr)

        # Start by rendering Top Level VPCs (those are the main containers)
        vpcs = [addr for addr, c in clusters.items() if c['type'] == 'vpc']
        for vpc_addr in vpcs:
            render_cluster(vpc_addr)
            
        # Render Global nodes (those with no parent cluster)
        global_nodes = [addr for addr, node in nodes.items() if node['parent_addr'] is None]
        for node_addr in global_nodes:
            node_data = nodes[node_addr]
            cls = node_data['diagram_class']
            node_instances[node_addr] = cls(node_data['label'])
    
    print(f"Diagram created: {output_filename}.{outformat}")

    # =========================================================================
    # Step 4: Generate Python Script (Optional)
    # =========================================================================
    if save_script:
        def sanitize_var_name(address):
            """Converts a resource address into a valid Python variable name."""
            clean = re.sub(r'[^a-zA-Z0-9_]', '_', address)
            if clean[0].isdigit(): clean = "_" + clean
            return clean

        lines = []
        
        # Collect imports dynamically based on used classes
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
        
        # Recursive script writer for clusters
        def render_cluster_script(cluster_addr, indent_level):
            indent = "    " * indent_level
            cluster_data = clusters[cluster_addr]
            label = cluster_data['label'].replace('"', '"')
            
            lines.append(f'{indent}with Cluster("{label}"):')
            
            # Nodes in cluster
            cluster_node_addrs = [addr for addr, node in nodes.items() if node['parent_addr'] == cluster_addr]
            for node_addr in cluster_node_addrs:
                node_data = nodes[node_addr]
                cls_name = node_data['diagram_class'].__name__
                node_label_repr = repr(node_data['label'])
                var_name = sanitize_var_name(node_addr)
                node_vars[node_addr] = var_name
                
                lines.append(f'{indent}    {var_name} = {cls_name}({node_label_repr})')
                
            # Child Clusters (Subnets in VPC)
            if cluster_data['type'] == 'vpc':
                 child_subnets = []
                 for sub_addr, sub in clusters.items():
                     if sub['type'] == 'subnet':
                         res = next(r for r in resources if r['address'] == sub_addr)
                         if find_parent_cluster(res.get('expressions', {})) == cluster_addr:
                             child_subnets.append(sub_addr)
                 
                 for sub_addr in child_subnets:
                     render_cluster_script(sub_addr, indent_level + 1)

        # Script for Top Level VPCs
        for vpc_addr in vpcs:
            render_cluster_script(vpc_addr, 1)
            
        # Script for Global nodes
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
