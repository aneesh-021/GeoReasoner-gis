# gepro/grass_utils.py
import subprocess
from typing import Dict, Any

def handle_grass(command: str, params: Dict[str, Any], context: Dict[str, Any]) -> Any:
    """Handle GRASS GIS commands."""
    
    grass_cmd = command  # e.g., 'r.slope.aspect'
    input_file = params.get('input')
    output_file = params.get('output')
    options = params.get('options', {})
    
    # GRASS --exec requires a specific setup. We assume the user has a GRASS location ready
    # or is running this within a GRASS session.
    cmd = ['grass', '--exec', grass_cmd]
    
    if input_file:
        # Some GRASS tools use 'input=' others use 'elevation=' etc. 
        # But we'll stick to 'input' as a generic parameter for our DSL
        cmd.append(f'input={input_file}')
        
    if output_file:
        cmd.append(f'output={output_file}')
    
    for key, value in options.items():
        cmd.append(f'{key}={value}')
    
    print(f"Executing GRASS: {' '.join(cmd)}")
    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode != 0:
        raise RuntimeError(f"GRASS command failed: {result.stderr}")
    
    return output_file or result.stdout
