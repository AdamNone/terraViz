from diagrams import Diagram, Cluster, Edge
from src.resources.registry import get_resource_handler
import json

def create_diagram(plan_path, output_filename="gcp_infra_diagram", show=False, outformat="png"):
    with open(plan_path, 'r') as f:
        plan = json.load(f)

    resources = plan.get('configuration', {}).get('root_module', {}).get('resources', [])
    
    nodes = {}  # address -> {handler, parent_addr}
    clusters = {} # address -> {type: 'vpc'|'subnet', label: str}
    edges = [] # (source_addr, target_addr)

    # 1. Identify Clusters (VPCs and Subnets) & Create Handlers
    for res in resources:
        res_type = res['type']
        address = res['address']
        
        handler = get_resource_handler(res)
        
        # We assume handlers exist for network/subnet even if we don't draw nodes for them
        # so we can use get_label()
        
        if res_type == 'google_compute_network':
            label = handler.get_label() if handler else res['name']
            clusters[address] = {'type': 'vpc', 'label': label}
        elif res_type == 'google_compute_subnetwork':
             label = handler.get_label() if handler else res['name']
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
        
        # Skip cluster resources (networks/subnets) as nodes, unless we want to show them BOTH as cluster and node.
        # Usually we don't.
        if res_type in ['google_compute_network', 'google_compute_subnetwork']:
            continue

        handler = get_resource_handler(res)
        
        if handler:
            # Find parent
            expressions = res.get('expressions', {})
            parent_addr = find_parent_cluster(expressions)
            
            nodes[address] = {'handler': handler, 'parent_addr': parent_addr}

    # 3. Identify Edges (Dependencies)
    for res in resources:
        source_addr = res['address']
        if source_addr not in nodes: continue
        
        expressions = res.get('expressions', {})
        
        # Deep search for references to other NODES (not clusters)
        def search_node_refs(expr_data):
            found = []
            if isinstance(expr_data, dict):
                if 'references' in expr_data:
                    found.extend(expr_data['references'])
                for v in expr_data.values():
                    found.extend(search_node_refs(v))
            elif isinstance(expr_data, list):
                for v in expr_data:
                    found.extend(search_node_refs(v))
            return found

        refs = search_node_refs(expressions)
        
        for ref in refs:
             for target_addr in nodes:
                 if source_addr == target_addr: continue
                 if ref == target_addr or ref.startswith(target_addr + "."):
                     # Found a dependency: Source -> Target
                     edges.append((source_addr, target_addr))

    # 4. Render Diagram
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
            # Use the detailed label from the handler
            with Cluster(cluster_data["label"]):
                # Instantiate nodes belonging to this cluster
                cluster_node_addrs = [addr for addr, node in nodes.items() if node['parent_addr'] == cluster_addr]
                for node_addr in cluster_node_addrs:
                    node_data = nodes[node_addr]
                    handler = node_data['handler']
                    # Create the node using handler's label and class
                    node_instances[node_addr] = handler.diagram_class(handler.get_label())
                
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
            handler = node_data['handler']
            node_instances[node_addr] = handler.diagram_class(handler.get_label())

        # Edges
        for src, dst in set(edges):
            if src in node_instances and dst in node_instances:
                # We could potentially get edge labels from handlers if we extended the system further
                node_instances[src] >> node_instances[dst]
    
    print(f"Diagram created: {output_filename}.{outformat}")