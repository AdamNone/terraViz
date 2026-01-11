terraform {
  required_providers {
    google = {
      source  = "hashicorp/google"
      version = ">= 4.0.0"
    }
  }
}

provider "google" {
  project     = var.project_id
  region      = var.region
  zone        = var.zone
  credentials = file(var.gcp_credentials_path)
}

module "compute_engine" {
  source     = "./modules/compute_engine"
  project_id = var.project_id
  region     = var.region
  zone       = var.zone
}
