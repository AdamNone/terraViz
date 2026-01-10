from diagrams import Diagram, Cluster
from src.mapper import get_diagram_node
import json

def create_diagram(plan_path, output_filename="gcp_infra_diagram", show=True):
    with open(plan_path, 'r') as f:
        plan = json.load(f)

    resources = plan.get('configuration', {}).get('root_module', {}).get('resources', [])
    
    nodes = {}  # address -> {class_ref, name, parent_addr}
    clusters = {} # address -> {type: 'vpc'|'subnet', name: str}
    edges = [] # (source_addr, target_addr)

    # 1. Identify Clusters (VPCs and Subnets)
    for res in resources:
        res_type = res['type']
        address = res['address']
        
        name_val = res['name']
        if 'expressions' in res and 'name' in res['expressions']:
            if 'constant_value' in res['expressions']['name']:
                name_val = res['expressions']['name']['constant_value']
        
        if res_type == 'google_compute_network':
            clusters[address] = {'type': 'vpc', 'name': name_val}
        elif res_type == 'google_compute_subnetwork':
             clusters[address] = {'type': 'subnet', 'name': name_val}

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

    # 2. Identify Nodes and Assign to Clusters
    for res in resources:
        res_type = res['type']
        address = res['address']
        
        # Name resolution
        name_val = res['name']
        if 'expressions' in res and 'name' in res['expressions']:
            if 'constant_value' in res['expressions']['name']:
                name_val = res['expressions']['name']['constant_value']
        
        # Use mapper to get the Diagram class
        diagram_class = get_diagram_node(res_type)
        
        if diagram_class:
            # Find parent
            expressions = res.get('expressions', {})
            parent_addr = find_parent_cluster(expressions)
            
            nodes[address] = {'class_ref': diagram_class, 'name': name_val, 'parent_addr': parent_addr}

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

    # 4. Render Diagram Directly
    node_instances = {} # address -> instantiated Diagram node object
    
    # We use a graph attribute to control direction or other viz properties if needed
    graph_attr = {
        "fontsize": "20"
    }

    with Diagram("Terraform Infrastructure", show=show, filename=output_filename, graph_attr=graph_attr):
        
        # Recursive writer for clusters
        def render_cluster(cluster_addr):
            cluster_data = clusters[cluster_addr]
            with Cluster(cluster_data["name"]):
                # Instantiate nodes belonging to this cluster
                cluster_node_addrs = [addr for addr, node in nodes.items() if node['parent_addr'] == cluster_addr]
                for node_addr in cluster_node_addrs:
                    node_data = nodes[node_addr]
                    # Create the node!
                    node_instances[node_addr] = node_data['class_ref'](node_data['name'])
                
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
            node_instances[node_addr] = node_data['class_ref'](node_data['name'])

        # Edges
        for src, dst in set(edges):
            if src in node_instances and dst in node_instances:
                node_instances[src] >> node_instances[dst]
    
    print(f"Diagram created: {output_filename}.png")