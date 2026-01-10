from src.generator import generate_diagram_script
import sys

if __name__ == "__main__":
    if len(sys.argv) < 3:
        print("Usage: python main.py <path_to_tfplan.json> <output_script.py>")
        # Default for convenience/testing if arguments not provided
        # But for CLI usage, it's better to be explicit or provide defaults.
        # Let's provide the default as in the previous script for backward compat/ease.
        print("Using defaults: terraform_infra/tfplan.json -> viz_from_plan.py")
        generate_diagram_script("terraform_infra/tfplan.json", "viz_from_plan.py")
    else:
        generate_diagram_script(sys.argv[1], sys.argv[2])
