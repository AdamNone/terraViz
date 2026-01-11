terraform {
  required_providers {
    google = {
      source  = "hashicorp/google"
      version = ">= 4.0.0"
    }
  }
}

provider "google" {
  project     = "my-gcp-project-id"
  region      = "us-central1"
  zone        = "us-central1-a"
  credentials = file(var.gcp_credentials_path)
}

# Network
resource "google_compute_network" "vpc_network" {
  name                    = "main-vpc"
  auto_create_subnetworks = false
}

resource "google_compute_subnetwork" "subnet" {
  name          = "main-subnet"
  ip_cidr_range = "10.0.1.0/24"
  region        = "us-central1"
  network       = google_compute_network.vpc_network.id
}

# Firewall
resource "google_compute_firewall" "allow_ssh_http" {
  name    = "allow-ssh-http"
  network = google_compute_network.vpc_network.name

  allow {
    protocol = "tcp"
    ports    = ["22", "80", "443"]
  }

  source_ranges = ["0.0.0.0/0"]
}

# Storage
resource "google_storage_bucket" "app_bucket" {
  name          = "my-app-static-assets-bucket"
  location      = "US"
  force_destroy = true

  uniform_bucket_level_access = true
}

# Database
resource "google_sql_database_instance" "main_db_instance" {
  name             = "main-db-instance"
  database_version = "POSTGRES_14"
  region           = "us-central1"

  settings {
    tier = "db-f1-micro"
    ip_configuration {
      ipv4_enabled    = false
      private_network = google_compute_network.vpc_network.id
    }
  }
  deletion_protection  = false
}

resource "google_sql_database" "database" {
  name     = "app-database"
  instance = google_sql_database_instance.main_db_instance.name
}

# Compute Service
resource "google_compute_instance" "web_server" {
  name         = "web-server-instance"
  machine_type = "e2-micro"
  zone         = "us-central1-a"

  boot_disk {
    initialize_params {
      image = "debian-cloud/debian-11"
    }
  }

  network_interface {
    network    = google_compute_network.vpc_network.id
    subnetwork = google_compute_subnetwork.subnet.id

    access_config {
      # Ephemeral public IP
    }
  }

  service_account {
    scopes = ["cloud-platform"]
  }

  tags = ["web-server", "http-server"]
}

resource "google_project_service" "compute_api" {
  service = "compute.googleapis.com"
  disable_on_destroy = false
}

resource "google_project_service" "sqladmin_api" {
  service = "sqladmin.googleapis.com"
  disable_on_destroy = false
}
