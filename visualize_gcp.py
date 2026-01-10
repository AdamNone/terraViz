from diagrams import Diagram, Cluster
from diagrams.gcp.compute import ComputeEngine
from diagrams.gcp.database import SQL
from diagrams.gcp.storage import Storage
from diagrams.gcp.network import VPC, FirewallRules

with Diagram("GCP Infrastructure", show=False, filename="gcp_infra_diagram"):
    with Cluster("main-vpc"):
        firewall = FirewallRules("allow-ssh-http")
        
        with Cluster("main-subnet"):
            web_server = ComputeEngine("web-server-instance")
            
        db = SQL("main-db-instance")
        
    bucket = Storage("app-bucket")

    # Connections
    firewall >> web_server
    web_server >> db
    web_server >> bucket
