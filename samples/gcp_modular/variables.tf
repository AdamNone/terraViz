variable "gcp_credentials_path" {
  description = "Path to the GCP credentials JSON file"
  type        = string
}

variable "project_id" {
  description = "GCP Project ID"
  type        = string
  default     = "my-gcp-project-id"
}

variable "region" {
  description = "GCP Region"
  type        = string
  default     = "us-central1"
}

variable "zone" {
  description = "GCP Zone"
  type        = string
  default     = "us-central1-a"
}
