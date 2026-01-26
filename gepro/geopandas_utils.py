# gepro/geopandas_utils.py
import os
from typing import Dict, Any, Optional

import geopandas as gpd

def is_placeholder(name: str) -> bool:
    """Check if a string is a common LLM placeholder."""
    if not isinstance(name, str): return False
    placeholders = ["v1", "v2", "var", "input", "gdf", "data", "a", "b", "target", "output"]
    return name.lower() in placeholders

def handle_geopandas(command: str, params: Dict[str, Any], context: Dict[str, Any]) -> Any:
    """Handle GeoPandas commands."""
    
    # Aliases for common LLM hallucinations
    cmd_lower = command.lower()
    if cmd_lower in ['intersect', 'intersection', 'overlay']: command = 'overlay'
    if cmd_lower in ['reproject', 'project', 'to_crs', 'geom_transform', 'transform']: command = 'to_crs'
    if cmd_lower in ['save', 'write', 'to_file', 'write_file']: command = 'to_file'

    def get_gdf(key_names: list, fallback: Optional[str] = None):
        """Robust GDF lookup with placeholder detection."""
        for key in key_names:
            val = params.get(key)
            if val and not is_placeholder(val):
                res = context.get(val)
                if res is not None: return res
        
        # Fallback to last result if provided or if placeholders were used
        if fallback:
            res = context.get(fallback)
            if res is not None: return res
        
        # Last resort: absolute last result from context
        last_res_key = context.get('_last_res')
        if last_res_key:
            return context.get(last_res_key)
        return None

    if command == 'read_file':
        filepath = params.get('filepath') or params.get('path') or params.get('input')
        if not filepath:
            raise ValueError("read_file requires a 'filepath' or 'path' parameter")
        return gpd.read_file(filepath)
    
    elif command == 'to_crs':
        gdf = get_gdf(['gdf', 'input', 'a', 'data'])
        crs = params.get('crs') or params.get('target_crs') or params.get('dst_crs') or params.get('out_crs')
        if gdf is None:
            raise ValueError("GeoDataFrame not found in context")
        if not crs:
            crs = params.get('target_coords') or params.get('dst')
        if not crs:
             raise ValueError("to_crs requires a CRS parameter")
        return gdf.to_crs(crs)
    
    elif command == 'to_file':
        gdf = get_gdf(['gdf', 'input', 'a', 'data'])
        filepath = params.get('filepath') or params.get('path') or params.get('output')
        if gdf is None:
            raise ValueError("GeoDataFrame not found in context")
        if not filepath:
            raise ValueError("to_file requires a 'filepath' or 'path' parameter")
        os.makedirs(os.path.dirname(filepath), exist_ok=True)
        gdf.to_file(filepath)
        return filepath
    
    elif command == 'buffer':
        gdf = get_gdf(['gdf', 'input', 'a', 'data'])
        distance = params.get('distance') or params.get('dist') or 0
        if gdf is None:
            raise ValueError("GeoDataFrame not found in context")
        buffered_gdf = gdf.copy()
        buffered_gdf['geometry'] = buffered_gdf.geometry.buffer(float(distance))
        return buffered_gdf
    
    elif command == 'clip':
        gdf = get_gdf(['gdf', 'input', 'a', 'data'])
        mask_name = params.get('mask') or params.get('cutline')
        mask = context.get(mask_name)
        if gdf is None or mask is None:
            raise ValueError("GeoDataFrame or mask not found in context")
        return gpd.clip(gdf, mask)
    
    elif command == 'overlay':
        gdf1_val = params.get('gdf1') or params.get('input1') or params.get('a')
        gdf2_val = params.get('gdf2') or params.get('input2') or params.get('b')
        
        # Robust lookup for overlay
        gdf1 = context.get(gdf1_val) if gdf1_val and not is_placeholder(gdf1_val) else None
        if gdf1 is None: gdf1 = get_gdf(['gdf1', 'input1', 'a']) 
        
        gdf2 = context.get(gdf2_val) if gdf2_val and not is_placeholder(gdf2_val) else None
        
        how = params.get('how') or params.get('operation') or 'intersection'
        if gdf1 is None or gdf2 is None:
            raise ValueError("GeoDataFrames not found in context")
        return gpd.overlay(gdf1, gdf2, how=how)

    elif command in ['filter', 'query']:
        gdf = get_gdf(['gdf', 'input', 'a', 'data'])
        condition = params.get('where') or params.get('condition') or params.get('query')
        if gdf is None:
            raise ValueError("GeoDataFrame not found in context")
        if not condition:
            raise ValueError("filter/query requires a condition")
        return gdf.query(condition)

    elif command in ['calculate', 'compute']:
        gdf = get_gdf(['gdf', 'input', 'a', 'data'])
        expr = params.get('expression') or params.get('expr')
        if gdf is None:
            raise ValueError("GeoDataFrame not found in context")
        if expr == 'area':
             # Return the total sum of areas as a float for the AI to interpret
             return float(gdf.geometry.area.sum())
        return eval(f"gdf.{expr}")

    elif command == 'dissolve':
        gdf = get_gdf(['gdf', 'input', 'a', 'data'])
        by = params.get('by')
        aggfunc = params.get('aggfunc', 'first')
        if gdf is None:
            raise ValueError("GeoDataFrame not found in context")
        return gdf.dissolve(by=by, aggfunc=aggfunc)

    elif command == 'sjoin':
        left_name = params.get('left') or params.get('gdf1') or params.get('input1') or params.get('a') or context.get('_last_res')
        right_name = params.get('right') or params.get('gdf2') or params.get('input2') or params.get('b')
        how = params.get('how', 'inner')
        predicate = params.get('predicate', 'intersects')
        left = context.get(left_name)
        right = context.get(right_name)
        if left is None or right is None:
            raise ValueError("GeoDataFrames not found in context")
        return gpd.sjoin(left, right, how=how, predicate=predicate)
    
    else:
        raise ValueError(f"Unknown geopandas command: {command}")
