import json
from src.mapper import get_diagram_node

def generate_diagram_script(plan_path, output_script_path):
    with open(plan_path, 'r') as f:
        plan = json.load(f)

    resources = plan.get('configuration', {}).get('root_module', {}).get('resources', [])
    
    nodes = {}  # address -> {class_name, name, var_name, parent_addr}
    clusters = {} # address -> {type: 'vpc'|'subnet', name: str, children: [], var_name: str}
    edges = [] # (source_var, target_var)
    used_imports = set(["from diagrams import Diagram, Cluster"])

    # 1. Identify Clusters (VPCs and Subnets)
    for res in resources:
        res_type = res['type']
        address = res['address']
        
        name_val = res['name']
        if 'expressions' in res and 'name' in res['expressions']:
            if 'constant_value' in res['expressions']['name']:
                name_val = res['expressions']['name']['constant_value']
        
        # We explicitly treat networks and subnets as Clusters
        if res_type == 'google_compute_network':
            clusters[address] = {'type': 'vpc', 'name': name_val, 'children': [], 'var_name': f"vpc_{res['name'].replace('-', '_')}"}
        elif res_type == 'google_compute_subnetwork':
             clusters[address] = {'type': 'subnet', 'name': name_val, 'children': [], 'var_name': f"subnet_{res['name'].replace('-', '_')}"}

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
            class_name = diagram_class.__name__
            module_name = diagram_class.__module__
            var_name = f"{class_name.lower()}_{res['name'].replace('-', '_')}"
            
            # Add dynamic import
            used_imports.add(f"from {module_name} import {class_name}")
            
            # Find parent
            expressions = res.get('expressions', {})
            parent_addr = find_parent_cluster(expressions)
            
            nodes[address] = {'class_name': class_name, 'name': name_val, 'var_name': var_name, 'parent_addr': parent_addr}

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
                     edges.append((nodes[source_addr]['var_name'], nodes[target_addr]['var_name']))

    # 4. Generate Code
    lines = []
    lines.extend(sorted(list(used_imports)))
    lines.append("")
    lines.append(f'with Diagram("Terraform Plan Infrastructure", show=False, filename="tf_plan_diagram"):')
    
    written_nodes = set()

    # Recursive writer for clusters
    def write_cluster(cluster_addr, indent_level=1):
        indent = "    " * indent_level
        cluster = clusters[cluster_addr]
        lines.append(f'{indent}with Cluster("{cluster["name"]}"):')
        
        # Write nodes belonging to this cluster
        cluster_nodes = [addr for addr, node in nodes.items() if node['parent_addr'] == cluster_addr]
        for node_addr in cluster_nodes:
            node = nodes[node_addr]
            lines.append(f'{indent}    {node["var_name"]} = {node["class_name"]}("{node["name"]}")')
            written_nodes.add(node_addr)
            
        # Write child clusters (Subnets inside VPCs)
        if cluster['type'] == 'vpc':
             # Find subnets that reference this VPC
             child_subnets = []
             for sub_addr, sub in clusters.items():
                 if sub['type'] == 'subnet':
                     res = next(r for r in resources if r['address'] == sub_addr)
                     if find_parent_cluster(res.get('expressions', {})) == cluster_addr:
                         child_subnets.append(sub_addr)
             
             for sub_addr in child_subnets:
                 write_cluster(sub_addr, indent_level + 1)

    # Top Level VPCs
    vpcs = [addr for addr, c in clusters.items() if c['type'] == 'vpc']
    for vpc_addr in vpcs:
        write_cluster(vpc_addr)
        
    # Global nodes (no parent)
    global_nodes = [addr for addr, node in nodes.items() if node['parent_addr'] is None]
    for node_addr in global_nodes:
        node = nodes[node_addr]
        lines.append(f'    {node["var_name"]} = {node["class_name"]}("{node["name"]}")')
        written_nodes.add(node_addr)

    lines.append("")
    lines.append("    # Edges")
    for src, dst in set(edges):
        lines.append(f"    {src} >> {dst}")

    with open(output_script_path, 'w') as f:
        f.write("\n".join(lines))
    
    print(f"Generated {output_script_path}")
