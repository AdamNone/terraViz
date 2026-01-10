import json
import re

# Mapping Terraform resources to Diagram classes
TF_TO_DIAGRAMS = {
    "google_compute_instance": "ComputeEngine",
    "google_sql_database_instance": "SQL",
    "google_storage_bucket": "Storage",
    "google_compute_firewall": "FirewallRules",
    "google_sql_database": "SQL", # Logical DB
}

# Imports required for the generated script
DIAGRAM_IMPORTS = {
    "ComputeEngine": "from diagrams.gcp.compute import ComputeEngine",
    "SQL": "from diagrams.gcp.database import SQL",
    "Storage": "from diagrams.gcp.storage import Storage",
    "FirewallRules": "from diagrams.gcp.network import FirewallRules",
}

def generate_diagram_script(plan_path, output_script_path):
    with open(plan_path, 'r') as f:
        plan = json.load(f)

    resources = plan.get('configuration', {}).get('root_module', {}).get('resources', [])
    
    # Store parsed nodes
    nodes = {}  # address -> {class, name, var_name, parent_addr}
    clusters = {} # address -> {type: 'vpc'|'subnet', name: str, children: [], var_name: str}
    edges = [] # (source_var, target_var)

    # 1. Identify Clusters (VPCs and Subnets)
    for res in resources:
        res_type = res['type']
        address = res['address']
        # Get the actual name value from expressions if available, else use resource name
        # In tfplan, constant_value is often where the name is
        name_val = res['name'] # default to alias
        if 'expressions' in res and 'name' in res['expressions']:
            if 'constant_value' in res['expressions']['name']:
                name_val = res['expressions']['name']['constant_value']
        
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
    used_imports = set(["from diagrams import Diagram, Cluster"])

    for res in resources:
        res_type = res['type']
        address = res['address']
        
        # Name resolution
        name_val = res['name']
        if 'expressions' in res and 'name' in res['expressions']:
            if 'constant_value' in res['expressions']['name']:
                name_val = res['expressions']['name']['constant_value']
        
        if res_type in TF_TO_DIAGRAMS:
            diagram_class = TF_TO_DIAGRAMS[res_type]
            var_name = f"{diagram_class.lower()}_{res['name'].replace('-', '_')}"
            
            used_imports.add(DIAGRAM_IMPORTS[diagram_class])
            
            # Find parent
            expressions = res.get('expressions', {})
            parent_addr = find_parent_cluster(expressions)
            
            # Special handling: SQL Instances often reference VPCs (private IP) but aren't "inside" them in the same way VMs are. 
            # But visually it makes sense to put them in the VPC or Subnet if referenced.
            
            nodes[address] = {'class': diagram_class, 'name': name_val, 'var_name': var_name, 'parent_addr': parent_addr}

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
            lines.append(f'{indent}    {node["var_name"]} = {node["class"]}("{node["name"]}")')
            written_nodes.add(node_addr)
            
        # Write child clusters (Subnets inside VPCs)
        if cluster['type'] == 'vpc':
             # Find subnets that reference this VPC
             child_subnets = []
             for sub_addr, sub in clusters.items():
                 if sub['type'] == 'subnet':
                     # We need to check the subnet resource for ref to this VPC
                     # Optimization: we can just check 'parent_ref' if we stored it for clusters too.
                     # Let's just quick check resources list again or store it earlier.
                     # Doing a quick lookup:
                     res = next(r for r in resources if r['address'] == sub_addr)
                     if find_parent_cluster(res.get('expressions', {})) == cluster_addr:
                         child_subnets.append(sub_addr)
             
             for sub_addr in child_subnets:
                 write_cluster(sub_addr, indent_level + 1)

    # Top Level VPCs
    vpcs = [addr for addr, c in clusters.items() if c['type'] == 'vpc']
    for vpc_addr in vpcs:
        write_cluster(vpc_addr)
        
    # Top Level Subnets (orphaned)
    subnets = [addr for addr, c in clusters.items() if c['type'] == 'subnet']
    # Check if subnet was already written (referenced by a VPC) - wait, my recursive writer doesn't track written CLUSTERS.
    # We should.
    
    # Better approach: Just iterate top-level containers (VPCs + Global)
    # Global nodes (no parent)
    global_nodes = [addr for addr, node in nodes.items() if node['parent_addr'] is None]
    for node_addr in global_nodes:
        node = nodes[node_addr]
        lines.append(f'    {node["var_name"]} = {node["class"]}("{node["name"]}")')
        written_nodes.add(node_addr)

    lines.append("")
    lines.append("    # Edges")
    for src, dst in set(edges):
        lines.append(f"    {src} >> {dst}")

    with open(output_script_path, 'w') as f:
        f.write("\n".join(lines))
    
    print(f"Generated {output_script_path}")

if __name__ == "__main__":
    generate_diagram_script("terraform_infra/tfplan.json", "viz_from_plan.py")
