from diagrams.gcp.analytics import BigQuery, Composer, DataFusion, Dataflow, Dataproc, PubSub
from diagrams.gcp.api import APIGateway, Apigee, Endpoints
from diagrams.gcp.compute import AppEngine, ComputeEngine, Functions, KubernetesEngine, Run
from diagrams.gcp.database import Bigtable, Firestore, Memorystore, Spanner, SQL
from diagrams.gcp.devtools import Build, ContainerRegistry, Scheduler, SourceRepositories, Tasks
from diagrams.gcp.management import Project
from diagrams.gcp.network import Armor, CDN, DNS, ExternalIpAddresses, FirewallRules, LoadBalancing, NAT, Router, Routes, VirtualPrivateCloud, VPN
from diagrams.gcp.operations import Logging, Monitoring
from diagrams.gcp.security import Iam, KeyManagementService, SecretManager
from diagrams.gcp.storage import Filestore, PersistentDisk, Storage

# Mapping of Terraform resource types to Diagrams classes
TERRAFORM_GCP_MAPPING = {
    # Analytics
    "google_bigquery_dataset": BigQuery,
    "google_bigquery_table": BigQuery,
    "google_composer_environment": Composer,
    "google_data_fusion_instance": DataFusion,
    "google_dataflow_job": Dataflow,
    "google_dataproc_cluster": Dataproc,
    "google_pubsub_topic": PubSub,
    "google_pubsub_subscription": PubSub,

    # API
    "google_api_gateway_gateway": APIGateway,
    "google_apigee_organization": Apigee,
    "google_endpoints_service": Endpoints,

    # Compute
    "google_app_engine_application": AppEngine,
    "google_compute_instance": ComputeEngine,
    "google_cloudfunctions_function": Functions,
    "google_cloudfunctions2_function": Functions,
    "google_container_cluster": KubernetesEngine,
    "google_cloud_run_service": Run,
    "google_cloud_run_v2_service": Run,

    # Database
    "google_bigtable_instance": Bigtable,
    "google_firestore_database": Firestore,
    "google_redis_instance": Memorystore,
    "google_spanner_instance": Spanner,
    "google_sql_database_instance": SQL,

    # DevTools
    "google_cloudbuild_trigger": Build,
    "google_container_registry": ContainerRegistry,
    "google_artifact_registry_repository": ContainerRegistry,
    "google_cloud_scheduler_job": Scheduler,
    "google_sourcerepo_repository": SourceRepositories,
    "google_cloud_tasks_queue": Tasks,

    # Management
    "google_project": Project,

    # Network
    "google_compute_security_policy": Armor,
    "google_compute_backend_bucket": CDN,
    "google_dns_managed_zone": DNS,
    "google_compute_address": ExternalIpAddresses,
    "google_compute_global_address": ExternalIpAddresses,
    "google_compute_firewall": FirewallRules,
    "google_compute_forwarding_rule": LoadBalancing,
    "google_compute_target_pool": LoadBalancing,
    "google_compute_backend_service": LoadBalancing,
    "google_compute_router_nat": NAT,
    "google_compute_router": Router,
    "google_compute_route": Routes,
    "google_compute_network": VirtualPrivateCloud,
    "google_compute_subnetwork": VirtualPrivateCloud,
    "google_compute_vpn_gateway": VPN,
    "google_compute_vpn_tunnel": VPN,

    # Operations
    "google_logging_project_sink": Logging,
    "google_monitoring_alert_policy": Monitoring,

    # Security
    "google_service_account": Iam,
    "google_project_iam_member": Iam,
    "google_kms_key_ring": KeyManagementService,
    "google_kms_crypto_key": KeyManagementService,
    "google_secret_manager_secret": SecretManager,

    # Storage
    "google_filestore_instance": Filestore,
    "google_compute_disk": PersistentDisk,
    "google_storage_bucket": Storage,
}

def get_diagram_node(resource_type):
    """
    Returns the Diagram class for a given Terraform resource type.
    """
    return TERRAFORM_GCP_MAPPING.get(resource_type)
