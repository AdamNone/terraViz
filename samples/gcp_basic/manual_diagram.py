from diagrams import Diagram, Cluster, Edge
from diagrams.gcp.compute import ComputeEngine
from diagrams.gcp.database import SQL
from diagrams.gcp.network import FirewallRules
from diagrams.gcp.storage import Storage

# metadata can be added through:
# 1. Multi-line labels on nodes (Name, Type, Config)
# 2. Labels on Edges (Protocols, Ports)
# 3. Global graph attributes (theme, direction, spacing)

graph_attr = {
    "fontsize": "25",
    "bgcolor": "white",
    "splines": "ortho", # Orthogonal lines for cleaner look
    "nodesep": "1.0",
    "ranksep": "1.0",
}

with Diagram(
    "GCP Basic Sample (Detailed)", 
    show=False, 
    filename="output/gcp_basic_manual", 
    direction="LR", # Left to Right flow
    graph_attr=graph_attr
):
    with Cluster("VPC: main-vpc\n10.0.0.0/16"):
        firewall = FirewallRules("Firewall: allow-ssh-http\nPorts: 22, 80, 443\nSrc: 0.0.0.0/0")
        
        with Cluster("Subnet: main-subnet\n10.0.1.0/24"):
            web_server = ComputeEngine(
                "web-server-instance\ne2-micro\nExternal IP: Ephemeral"
            )
            
        db_instance = SQL(
            "main-db-instance\nPostgres 14\nPrivate IP Only"
        )
        
    bucket = Storage(
        "app-bucket\nLocation: US\nUniform Access: Enabled"
    )

    # Labeled Edges for metadata on connections
    firewall >> Edge(label="Allow TCP") >> web_server
    
    web_server >> Edge(label="Port 5432 (Private)", color="darkgreen", style="dashed") >> db_instance
    
    web_server >> Edge(label="HTTPS/Storage API", color="blue") >> bucket
