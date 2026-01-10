# GCP Basic Infrastructure Sample

This directory contains a sample Terraform configuration representing a standard 3-tier web application architecture on Google Cloud Platform (GCP).

## Architecture Overview

The `main.tf` defines the following resources:

### 1. Networking (`main-vpc`)
*   **VPC Network**: A custom Virtual Private Cloud named `main-vpc`.
*   **Subnetwork**: A dedicated subnet `main-subnet` (10.0.1.0/24) in `us-central1`.
*   **Firewall Rules**: `allow-ssh-http` permits ingress traffic on ports 22 (SSH), 80 (HTTP), and 443 (HTTPS) from any source (`0.0.0.0/0`).

### 2. Compute Layer
*   **Compute Engine Instance**: A `web-server-instance` (e2-micro) running Debian 11.
    *   It resides within `main-vpc` and `main-subnet`.
    *   It has an ephemeral public IP for access.
    *   Tagged with `web-server` and `http-server`.

### 3. Database Layer
*   **Cloud SQL Instance**: `main-db-instance` (PostgreSQL 14, db-f1-micro).
    *   Configured with a **Private IP** address within `main-vpc` (no public IP).
*   **Logical Database**: A standard PostgreSQL database named `app-database` created inside the instance.

### 4. Storage
*   **Cloud Storage Bucket**: `my-app-static-assets-bucket` for storing static assets.
    *   Location: US
    *   Uniform Bucket Level Access is enabled.

## Diagrams

### Auto-Generated Diagram
Run the following command from the project root to generate a diagram from the Terraform Plan:

```bash
python main.py samples/gcp_basic/tfplan.json png
```

This will create `output/gcp_basic.png`.

### Manual Baseline Diagram
A manual baseline script `manual_diagram.py` is provided to compare against the auto-generated version. It visualizes the intended relationships:

*   **Web Server** connects to **Cloud SQL**.
*   **Web Server** accesses **Cloud Storage**.
*   **Firewall** protects the **VPC/Instances**.

To generate the manual baseline:
```bash
python samples/gcp_basic/manual_diagram.py
```
This will create `output/gcp_basic_manual.png`.
