# TerraViz

TerraViz is an open-source tool designed to visualize Terraform infrastructure plans. It parses a `tfplan.json` file and generates a diagram representing the resources and their relationships (specifically for Google Cloud Platform).

## Project Structure

The repository is organized to separate core logic, resource mappings, and example configurations.

*   **`main.py`**: The entry point of the application. It parses command-line arguments and invokes the generator.
*   **`src/`**: Contains the source code for the visualization engine.
    *   **`generator.py`**: The core logic. It processes the JSON plan, identifies resources (Nodes) and container structures like VPCs and Subnets (Clusters), resolves relationships, and renders the diagram.
    *   **`mapper.py`**: A comprehensive mapping file that links Terraform resource types (e.g., `google_compute_instance`) to their corresponding classes in the `diagrams` library (e.g., `ComputeEngine`).
    *   **`utils.py`**: Helper functions for extracting values from the complex Terraform JSON structure.
    *   **`resources/`**: Contains specific logic for extracting labels and metadata from different resource types.
        *   **`lookup.py`**: A central registry that maps resource types to their specific label-generation functions.
        *   **`gcp/`**: Modules (e.g., `compute.py`, `database.py`) that export simple functions (like `get_label`) to formatting resource details.

### Why this architecture?
We separate `mapper.py` from `resources/` to keep simple 1-to-1 mappings lightweight. The `resources/` directory allows us to scale complex label generation logic without cluttering the main generator code. We avoided a heavy class-based hierarchy in favor of simple, functional components.

## Automatic Layout & Layering

To ensure the generated diagrams look professional and organized, TerraViz employs an automatic layering system.

### How it Works
The generator automatically categorizes every resource into one of five logical "buckets" (layers) based on its Terraform resource type:

1.  **Security**: Firewalls, IAM roles, KMS keys, WAFs.
2.  **Network**: VPCs, Subnets, Routers, Gateways, DNS, CDNs.
3.  **App**: Compute instances, Cloud Functions, Containers (Kubernetes/Cloud Run).
4.  **Data**: SQL Databases, Redis, BigTable, Firestore.
5.  **Storage**: Cloud Storage Buckets, Filestore, Disks.

### The "Invisible Edges" Technique
Graphviz (the engine underneath the `diagrams` library) attempts to optimize the graph layout automatically, which can sometimes result in chaotic, scattered diagrams.

To force a clean, **Left-to-Right** flow that mirrors standard architecture diagrams, TerraViz injects **Invisible Edges** (`style="invis"`) between the first item of each adjacent layer:

`Security Node` -> `Network Node` -> `App Node` -> `Data Node` -> `Storage Node`

These edges act as a skeleton for the graph, forcing the columns to align visually without drawing messy lines that clutter the final image.

## Local Development Setup

### Prerequisites
1.  **Python 3.8+**
2.  **Graphviz**: This tool requires Graphviz to be installed on your system (not just the python library).
    *   **macOS**: `brew install graphviz`
    *   **Ubuntu**: `sudo apt-get install graphviz`
    *   **Windows**: Download and install from the Graphviz website.

### Installation
1.  Clone the repository:
    ```bash
    git clone https://github.com/your-username/terraViz.git
    cd terraViz
    ```

2.  Create and activate a virtual environment:
    ```bash
    python -m venv .venv
    source .venv/bin/activate  # On Windows: .venv\Scripts\activate
    ```

3.  Install Python dependencies:
    ```bash
    pip install -r requirements.txt
    ```

## Generating a Terraform Plan

To use this tool, you first need a JSON-formatted Terraform plan.

1.  **Set up Credentials**:
    The sample projects (`samples/gcp_basic`) require a GCP Service Account key. 
    
    *   Create a directory for your secrets (it is already ignored in `.gitignore`):
        ```bash
        mkdir secrets
        ```
    *   Place your Google Cloud Service Account JSON key in this directory (e.g., `secrets/gcp_key.json`).
    *   **Note**: If you don't have a real key but just want to test the *structure*, you can use a dummy file. Terraform requires a valid-looking JSON structure even if you aren't actually applying changes to GCP.
    
    You can create a file at `secrets/gcp_key.json` with the following content:
    ```json
    {
      "type": "service_account",
      "project_id": "my-gcp-project-id",
      "private_key_id": "1234567890abcdef1234567890abcdef12345678",
      "private_key": "-----BEGIN PRIVATE KEY-----\nMIIEvgIBADANBgkqhkiG9w0BAQEFAASCBKgwggSkAgEAAoIBAQDh\n-----END PRIVATE KEY-----",
      "client_email": "dummy@my-gcp-project-id.iam.gserviceaccount.com",
      "client_id": "123456789012345678901",
      "auth_uri": "https://accounts.google.com/o/oauth2/auth",
      "token_uri": "https://oauth2.googleapis.com/token",
      "auth_provider_x509_cert_url": "https://www.googleapis.com/oauth2/v1/certs",
      "client_x509_cert_url": "https://www.googleapis.com/robot/v1/metadata/x509/dummy%40my-gcp-project-id.iam.gserviceaccount.com"
    }
    ```

2.  **Configure Terraform**:
    Navigate to the sample directory and create a `terraform.tfvars` file (or edit the existing one) to point to your key.

    ```bash
    cd samples/gcp_basic
    # Create/Edit terraform.tfvars
    echo 'gcp_credentials_path = "../../secrets/gcp_key.json"' >> terraform.tfvars
    echo 'project_id = "your-gcp-project-id"' >> terraform.tfvars
    echo 'region = "us-central1"' >> terraform.tfvars
    ```

3.  **Generate the JSON Plan**:
    ```bash
    terraform init
    terraform plan -out=tfplan.binary
    terraform show -json tfplan > tfplan.json
    ```

## Usage

Run `main.py` from the root directory, passing the path to your generated `tfplan.json`.

### Basic Command
```bash
python main.py samples/gcp_basic/tfplan.json
```
This will generate `output/gcp_basic.png`.

### Changing Output Format
You can specify the output format (e.g., `jpg`, `dot`, `pdf`). Default is `png`.
```bash
python main.py samples/gcp_basic/tfplan.json jpg
```

### Generating a Python Script (`--save-script`)
If you want to tweak the diagram manually later, you can have the tool generate the Python code that reproduces the diagram.
```bash
python main.py samples/gcp_basic/tfplan.json --save-script
```
This will create `output/gcp_basic.py`. You can run this script independently:
```bash
python output/gcp_basic.py
```

## Contributing

1.  Fork the repo.
2.  Create a branch for your feature (`git checkout -b feature/amazing-feature`).
3.  Commit your changes.
4.  Push to the branch.
5.  Open a Pull Request.