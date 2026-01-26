# gepro/core.py
# Core entry point for executing gepro workflows.
# This module orchestrates the execution of modular tool handlers.

import yaml
from typing import Dict, Any, List, Optional

# Import modular handlers
from .geopandas_utils import handle_geopandas
from .gdal_utils import handle_gdal
from .grass_utils import handle_grass

# Global Registry
TOOL_HANDLERS = {
    'geopandas': handle_geopandas,
    'gdal': handle_gdal,
    'grass': handle_grass
}

def register_handler(name: str, handler_func):
    """Dynamically add new tool libraries to the engine."""
    TOOL_HANDLERS[name] = handler_func

def execute_workflow(workflow: Dict[str, Any]) -> Dict[str, Any]:
    """
    Executes a multi-library GIS workflow step-by-step.
    """
    if not isinstance(workflow, dict) or 'steps' not in workflow:
        raise ValueError("Invalid workflow format. Must be a dict with 'steps'.")

    context = {}
    last_res_key = None
    steps = workflow['steps']

    for i, step in enumerate(steps):
        # Validation for malformed YAML steps
        if not isinstance(step, dict):
            print(f"⚠️  Skipping malformed Step {i+1}: Not a dictionary.")
            continue
            
        tool_lib = step.get('tool')
        command = step.get('command')
        params = step.get('params', {})
        output_key = step.get('output')

        if not tool_lib or not command:
            print(f"⚠️  Skipping incomplete Step {i+1}: Missing 'tool' or 'command' keys.")
            continue
            
        # Inject the last result key into params for handlers to use if needed
        context['_last_res'] = last_res_key

        print(f"--- Running Step {i+1}: {tool_lib}.{command} ---")
        
        handler = TOOL_HANDLERS.get(tool_lib)
        if not handler:
            raise ValueError(f"Library '{tool_lib}' is not supported by gepro.")

        try:
            result = handler(command, params, context)
            if output_key:
                context[output_key] = result
                last_res_key = output_key
        except Exception as e:
            print(f"Critical error in step {i+1}: {str(e)}")
            raise e

    return context

def run_from_file(file_path: str):
    """Load and execute a workflow from a YAML file."""
    with open(file_path, 'r') as f:
        data = yaml.safe_load(f)
    return execute_workflow(data)
