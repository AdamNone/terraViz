"""
TerraViz Entry Point.

This module serves as the command-line interface (CLI) for the TerraViz tool.
It handles argument parsing, output directory setup, and invoking the core
diagram generation logic.

Usage:
    python main.py <path_to_tfplan.json> [output_format] [--save-script]
"""

from src.generator import create_diagram
import sys
import os
import argparse

def ensure_output_dir():
    """
    Ensures that the 'output' directory exists in the project root.
    
    Returns:
        str: The path to the output directory ("output").
    """
    output_dir = "output"
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)
    return output_dir

if __name__ == "__main__":
    # Initialize argument parser
    parser = argparse.ArgumentParser(description="Generate infrastructure diagrams from Terraform plan JSON.")
    
    # Required argument: Path to the JSON plan file
    parser.add_argument("plan_path", help="Path to the tfplan.json file")
    
    # Optional argument: Output format (default: png)
    parser.add_argument("output_format", nargs="?", default="png", help="Output format (png, jpg, dot, etc.). Default: png")
    
    # Optional flag: Save the Python script used to generate the diagram
    parser.add_argument("--save-script", action="store_true", help="Save the generated Python script for manual review")

    args = parser.parse_args()
    
    plan_path = args.plan_path
    output_format = args.output_format
    
    # Validate input file existence
    if not os.path.exists(plan_path):
        print(f"Error: Plan file '{plan_path}' not found.")
        sys.exit(1)

    # Determine Output Filename
    # We use the name of the directory containing the plan file as the basis for the output filename.
    # Example: samples/gcp_basic/tfplan.json -> output/gcp_basic.png
    
    plan_dir = os.path.dirname(os.path.abspath(plan_path))
    dir_name = os.path.basename(plan_dir)
    
    # Fallback if the file is in the current working directory
    if not dir_name or dir_name == ".":
         dir_name = "infra_diagram"
         
    # Setup output directory
    output_dir = ensure_output_dir()
    output_filename = os.path.join(output_dir, dir_name)
    
    print(f"Generating diagram for {plan_path}...")
    
    # Invoke the core generator function
    create_diagram(plan_path, output_filename=output_filename, outformat=output_format, save_script=args.save_script)
