# gepro/utils.py
# Utility functions for GIS data handling and chunk processing

import json
import os
from typing import List, Dict, Any, Optional

def load_chunks(filepath: str) -> List[Dict[str, Any]]:
    """Load chunks from a JSONL file."""
    chunks = []
    with open(filepath, 'r') as f:
        for line in f:
            if line.strip():
                chunks.append(json.loads(line))
    return chunks

def save_chunks(chunks: List[Dict[str, Any]], filepath: str) -> None:
    """Save chunks to a JSONL file."""
    with open(filepath, 'w') as f:
        for chunk in chunks:
            f.write(json.dumps(chunk) + '\n')

def deduplicate_chunks(chunks: List[Dict[str, Any]], key: str = 'tool') -> List[Dict[str, Any]]:
    """Remove duplicate chunks based on a key field."""
    seen = set()
    unique = []
    for chunk in chunks:
        k = chunk.get(key, '')
        if k and k not in seen:
            seen.add(k)
            unique.append(chunk)
    return unique

def clean_chunk(chunk: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    """
    Clean and validate a single chunk.
    Returns None if the chunk should be filtered out.
    """
    # Required fields
    tool = chunk.get('tool', '').strip()
    if not tool:
        return None
    
    # Filter out invalid entries
    invalid_patterns = [
        'fiona.path', 'path module', 'module', '.__', '/path',
        'ParsedPath', 'UnparsedPath', 'www.', 'http://', 'https://',
        '__pycache__', '.pyc', 'No such file'
    ]
    
    tool_lower = tool.lower()
    for pattern in invalid_patterns:
        if pattern.lower() in tool_lower:
            return None
    
    # Ensure all fields have values
    cleaned = {
        'tool': tool,
        'domain': chunk.get('domain', 'General').strip() or 'General',
        'type': chunk.get('type', 'Command-line').strip() or 'Command-line',
        'description': chunk.get('description', '').strip(),
        'usage': chunk.get('usage', '').strip(),
        'example': chunk.get('example', '').strip(),
        'link': chunk.get('link', '').strip()
    }
    
    # Generate better description if generic
    if not cleaned['description'] or 'Tool for geospatial processing:' in cleaned['description']:
        cleaned['description'] = generate_description(cleaned)
    
    # Generate better usage if missing
    if not cleaned['usage']:
        cleaned['usage'] = f"{tool} --help"
    
    # Generate example if missing
    if not cleaned['example']:
        cleaned['example'] = generate_example(cleaned)
    
    return cleaned

def generate_description(chunk: Dict[str, Any]) -> str:
    """Generate a more specific description based on keywords in the tool name."""
    tool = chunk.get('tool', '')
    domain = chunk.get('domain', 'General')
    
    tool_lower = tool.lower()
    
    # Specific common operations
    if 'buffer' in tool_lower:
        return f"{tool} - Spatial buffer operation to create a zone of a specified distance around geometries."
    elif 'intersect' in tool_lower:
        return f"{tool} - Spatial intersection operation to find the overlap between different layers/geometries."
    elif 'reproject' in tool_lower or 'warp' in tool_lower or 'transform' in tool_lower:
        return f"{tool} - Coordinate transformation or re-projection to change the spatial reference system."
    elif 'clip' in tool_lower:
        return f"{tool} - Spatial clipping operation to extract features within a boundary."
    elif 'overlay' in tool_lower:
        return f"{tool} - Spatial overlay operation (union, identity, symmetrical difference) between layers."
    elif 'slope' in tool_lower:
        return f"{tool} - Terrain analysis tool to calculate the rate of change in elevation (slope)."
    elif 'aspect' in tool_lower:
        return f"{tool} - Terrain analysis tool to calculate the downhill direction of the steepest slope."
    elif 'ndvi' in tool_lower:
        return f"{tool} - Normalized Difference Vegetation Index calculation for vegetation health analysis."
    
    # Domain-specific fallback
    domain_templates = {
        'Raster': f"{tool} - Raster processing tool for grid/image data analysis and transformation.",
        'Vector': f"{tool} - Vector processing tool for geometry operations and spatial analysis.",
        'Geometry': f"{tool} - Geometry tool for creating and analyzing spatial objects.",
        'Projection': f"{tool} - Coordinate reference system tool for transformations.",
        'Spatial SQL': f"{tool} - PostGIS spatial function for database-level operations.",
    }
    
    return domain_templates.get(domain, f"{tool} - Geospatial processing tool for {domain.lower()} operations.")

def generate_example(chunk: Dict[str, Any]) -> str:
    """Generate a meaningful example based on tool type and domain."""
    tool = chunk.get('tool', '')
    domain = chunk.get('domain', 'General')
    tool_type = chunk.get('type', '')
    
    if tool_type == 'Python API':
        return f"import geopandas as gpd\nresult = gpd.{tool}('input.shp')"
    elif tool_type == 'PostGIS Function':
        return f"SELECT {tool}(geom) FROM spatial_table;"
    elif domain == 'Raster':
        return f"{tool} input.tif output.tif --format GTiff"
    else:
        return f"{tool} input.shp output.shp"

def get_embedding_text(chunk: Dict[str, Any]) -> str:
    """
    Generate rich text for embedding that captures tool semantics.
    Combines multiple fields for better retrieval.
    """
    parts = []
    
    # Tool name with domain context
    tool = chunk.get('tool', '')
    domain = chunk.get('domain', '')
    tool_type = chunk.get('type', '')
    
    if tool:
        parts.append(f"Tool: {tool}")
    if domain:
        parts.append(f"Domain: {domain}")
    if tool_type:
        parts.append(f"Type: {tool_type}")
    
    # Description (most important for semantics)
    desc = chunk.get('description', '')
    if desc:
        parts.append(f"Description: {desc}")
    
    # Usage pattern
    usage = chunk.get('usage', '')
    if usage:
        parts.append(f"Usage: {usage}")
    
    # Example
    example = chunk.get('example', '')
    if example:
        parts.append(f"Example: {example}")
    
    return ' | '.join(parts)

def get_library_from_tool(tool: str, link: str = '') -> str:
    """Determine which GIS library a tool belongs to."""
    tool_lower = tool.lower()
    link_lower = link.lower()
    
    if 'gdal' in tool_lower or 'gdal' in link_lower or 'ogr' in tool_lower:
        return 'GDAL'
    elif 'grass' in link_lower or tool_lower.startswith('r.') or tool_lower.startswith('v.'):
        return 'GRASS'
    elif 'qgis' in link_lower or 'native:' in tool_lower:
        return 'QGIS'
    elif 'saga' in link_lower:
        return 'SAGA'
    elif 'postgis' in link_lower or tool_lower.startswith('st_'):
        return 'PostGIS'
    elif 'geopandas' in link_lower:
        return 'GeoPandas'
    elif 'rasterio' in link_lower:
        return 'Rasterio'
    elif 'shapely' in link_lower:
        return 'Shapely'
    elif 'fiona' in link_lower:
        return 'Fiona'
    elif 'pyproj' in link_lower:
        return 'PyProj'
    else:
        return 'Unknown'
def run_cleaning_pipeline(input_path: str, output_path: Optional[str] = None) -> Dict[str, Any]:
    """
    Run the data cleaning pipeline on chunks.
    
    Args:
        input_path: Path to input JSONL file
        output_path: Path to output JSONL file (optional, defaults to input_path)
        
    Returns:
        Stats dict with counts and info
    """
    if output_path is None:
        output_path = input_path
    
    print(f"Loading chunks from {input_path}...")
    chunks = load_chunks(input_path)
    original_count = len(chunks)
    
    print(f"Cleaning {original_count} chunks...")
    cleaned = []
    for chunk in chunks:
        result = clean_chunk(chunk)
        if result:
            cleaned.append(result)
    
    print(f"Deduplicating {len(cleaned)} chunks...")
    unique = deduplicate_chunks(cleaned)
    
    print(f"Saving {len(unique)} chunks to {output_path}...")
    save_chunks(unique, output_path)
    
    stats = {
        'original_count': original_count,
        'cleaned_count': len(cleaned),
        'unique_count': len(unique),
        'removed_count': original_count - len(unique),
        'output_path': output_path
    }
    
    print(f"\n✓ Pipeline complete!")
    print(f"  Original: {stats['original_count']}")
    print(f"  After cleaning: {stats['cleaned_count']}")
    print(f"  After dedup: {stats['unique_count']}")
    print(f"  Removed: {stats['removed_count']}")
    
    return stats
