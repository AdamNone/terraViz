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
  source           = "./modules/compute_engine"
  project_id       = var.project_id
  region           = var.region
  zone             = var.zone
  vpc_name         = var.vpc_name
  subnet_name      = var.subnet_name
  subnet_cidr      = var.subnet_cidr
  machine_type     = var.machine_type
  db_instance_name = var.db_instance_name
  bucket_name      = var.bucket_name
}