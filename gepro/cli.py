# gepro/cli.py
import sys
import argparse
from gepro.core import run_from_file

def main():
    parser = argparse.ArgumentParser(description="gepro: Modular GIS Workflow Executor")
    parser.add_argument('file', help="Path to the workflow.yaml file")
    
    args = parser.parse_args()
    
    try:
        print(f"🚀 Starting gepro engine for: {args.file}")
        run_from_file(args.file)
        print("✅ Workflow execution finished successfully.")
    except Exception as e:
        print(f"❌ Execution failed: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
