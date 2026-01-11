variable "project_id" {
  description = "The GCP Project ID"
  type        = string
}

variable "region" {
  description = "The GCP Region"
  type        = string
}

variable "zone" {
  description = "The GCP Zone"
  type        = string
}

variable "vpc_name" {
  description = "Name of the VPC network"
  type        = string
  default     = "main-vpc"
}

variable "subnet_name" {
  description = "Name of the subnetwork"
  type        = string
  default     = "main-subnet"
}

variable "subnet_cidr" {
  description = "CIDR block for the subnetwork"
  type        = string
  default     = "10.0.1.0/24"
}

variable "machine_type" {
  description = "Compute Engine machine type"
  type        = string
  default     = "e2-micro"
}

variable "db_instance_name" {
  description = "Name of the Cloud SQL instance"
  type        = string
  default     = "main-db-instance"
}

variable "bucket_name" {
  description = "Name of the Storage Bucket"
  type        = string
  default     = "my-app-static-assets-bucket"
}