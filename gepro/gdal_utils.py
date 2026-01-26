# gepro/gdal_utils.py
import subprocess
from typing import Dict, Any

def handle_gdal(command: str, params: Dict[str, Any], context: Dict[str, Any]) -> Any:
    """Handle GDAL commands via subprocess."""
    
    cmd_mapping = {
        'translate': 'gdal_translate',
        'warp': 'gdalwarp',
        'info': 'gdalinfo',
        'calc': 'gdal_calc.py',
        'merge': 'gdal_merge.py',
        'buildvrt': 'gdalbuildvrt',
    }
    
    gdal_cmd = cmd_mapping.get(command, command)
    input_file = params.get('input')
    output_file = params.get('output')
    options = params.get('options', [])
    
    cmd = [gdal_cmd]
    if isinstance(options, list):
        cmd.extend(options)
    elif isinstance(options, str):
        cmd.extend(options.split())
        
    if input_file:
        cmd.append(input_file)
    if output_file:
        cmd.append(output_file)
    
    print(f"Executing: {' '.join(cmd)}")
    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode != 0:
        raise RuntimeError(f"GDAL command failed: {result.stderr}")
    
    return output_file or result.stdout
