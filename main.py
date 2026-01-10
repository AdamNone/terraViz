from src.generator import create_diagram
import sys
import os

def ensure_output_dir():
    output_dir = "output"
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)
    return output_dir

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python main.py <path_to_tfplan.json> [output_format]")
        print("Example: python main.py samples/gcp_basic/tfplan.json png")
        sys.exit(1)
    
    plan_path = sys.argv[1]
    output_format = sys.argv[2] if len(sys.argv) > 2 else "png"
    
    # Check if plan file exists
    if not os.path.exists(plan_path):
        print(f"Error: Plan file '{plan_path}' not found.")
        sys.exit(1)

    # Derive output filename from directory name
    # e.g., samples/gcp_basic/tfplan.json -> gcp_basic
    # or just tfplan.json -> root (or current dir name)
    
    plan_dir = os.path.dirname(os.path.abspath(plan_path))
    dir_name = os.path.basename(plan_dir)
    
    # If file is in current dir (dir_name is same as cwd name or empty if just filename passed)
    if not dir_name or dir_name == ".":
         dir_name = "infra_diagram"
         
    output_dir = ensure_output_dir()
    output_filename = os.path.join(output_dir, dir_name)
    
    print(f"Generating diagram for {plan_path}...")
    create_diagram(plan_path, output_filename=output_filename, outformat=output_format)
