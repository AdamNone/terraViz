from diagrams import Diagram, Cluster
from diagrams.gcp.compute import ComputeEngine
from diagrams.gcp.database import SQL
from diagrams.gcp.network import FirewallRules
from diagrams.gcp.storage import Storage

with Diagram("Terraform Plan Infrastructure", show=False, filename="tf_plan_diagram"):
    with Cluster("main-vpc"):
        firewallrules_allow_ssh_http = FirewallRules("allow-ssh-http")
        sql_main_db_instance = SQL("main-db-instance")
        with Cluster("main-subnet"):
            computeengine_web_server = ComputeEngine("web-server-instance")
    sql_database = SQL("app-database")
    storage_app_bucket = Storage("my-app-static-assets-bucket")

    # Edges
    sql_database >> sql_main_db_instance