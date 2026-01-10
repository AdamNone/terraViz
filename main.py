from src.generator import create_diagram
import sys
import os

if __name__ == "__main__":
    if len(sys.argv) < 2:
        # Default behavior
        default_plan = "terraform_infra/tfplan.json"
        if os.path.exists(default_plan):
            print(f"Using default plan: {default_plan}")
            create_diagram(default_plan)
        else:
            print("Usage: python main.py <path_to_tfplan.json> [output_filename]")
            print(f"Error: Default file '{default_plan}' not found.")
            sys.exit(1)
    else:
        plan_path = sys.argv[1]
        output_name = sys.argv[2] if len(sys.argv) > 2 else "gcp_infra_diagram"
        create_diagram(plan_path, output_name)