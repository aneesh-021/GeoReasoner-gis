
# fetch_real_chunks.py
import requests
from bs4 import BeautifulSoup
import json
import time
import os
from datetime import datetime

# Output to your existing format
def save_chunks(chunks, filename="data/chunks.jsonl"):
    with open(filename, "a") as f:  # Append mode for continuous updates
        for chunk in chunks:
            f.write(json.dumps(chunk) + "\n")
    print(f"Added {len(chunks)} chunks to {filename}")

# Helper: Fetch and parse a page
def fetch_and_parse(url, selector_for_tools, desc_selector=None, example_selector=None):
    headers = {"User-Agent": "Mozilla/5.0 (compatible; GIS-Data-Bot/1.0)"}  # Polite scraping
    resp = requests.get(url, headers=headers)
    soup = BeautifulSoup(resp.text, "lxml")
    tools = []
    
    for tool_elem in soup.select(selector_for_tools):
        tool_name = tool_elem.text.strip()
        if not tool_name:
            continue
        
        # Default values (customize per library)
        domain = "Raster"  # Default; override below
        typ = "Command-line"  # Default
        desc = tool_elem.get("title", "") or f"Tool for geospatial processing: {tool_name}"
        usage = f"{tool_name} [options] input output"
        example = f"{tool_name} input.tif output.tif"
        link = url
        
        if desc_selector:
            desc_elem = tool_elem.select_one(desc_selector)
            desc = desc_elem.text.strip() if desc_elem else desc
        
        if example_selector:
            example_elem = tool_elem.select_one(example_selector)
            example = example_elem.text.strip() if example_elem else example
        
        tools.append({
            "tool": tool_name,
            "domain": domain,
            "type": typ,
            "description": desc[:200],  # Truncate for chunks
            "usage": usage,
            "example": example,
            "link": link
        })
    
    return tools

# Fetch from specific libraries (2025 sources)
def fetch_gdal():
    url = "https://gdal.org/en/stable/programs/index.html"
    selector = "a[href*='programs/']"  # Links to tools like gdal_translate
    return fetch_and_parse(url, selector, desc_selector="p")

def fetch_grass():
    url = "https://grass.osgeo.org/grass-stable/manuals/index.html"
    selector = "a[href*='manuals/']"  # Modules like r.slope.aspect
    domain = "Raster/Vector"
    tools = fetch_and_parse(url, selector)
    for t in tools:
        t["domain"] = domain
    return tools

def fetch_qgis():
    # Use R package for full list (or scrape wiki)
    url = "https://r-spatial.github.io/qgisprocess/reference/qgis_algorithms.html"
    selector = "code"  # Algorithm names like native:clip
    typ = "QGIS Processing Algorithm"
    tools = fetch_and_parse(url, selector)
    for t in tools:
        t["type"] = typ
    return tools

def fetch_saga():
    url = "https://saga-gis.sourceforge.io/saga_tool_doc/9.0.0/"  # 2025 version
    selector = "a[href*='html']"  # Tools like ta_morphometry
    return fetch_and_parse(url, selector)

def fetch_geopandas():
    url = "https://geopandas.org/en/stable/docs/reference.html"
    selector = "a[href*='api/']"  # Functions like read_file
    typ = "Python API"
    tools = fetch_and_parse(url, selector)
    for t in tools:
        t["type"] = typ
        t["domain"] = "Vector"
    return tools

def fetch_rasterio():
    url = "https://rasterio.readthedocs.io/en/latest/api/rasterio.html"
    selector = "a[href*='#rasterio.']"  # Functions like open
    typ = "Python API"
    tools = fetch_and_parse(url, selector)
    for t in tools:
        t["type"] = typ
        t["domain"] = "Raster"
    return tools

def fetch_shapely():
    url = "https://shapely.readthedocs.io/en/stable/manual.html"
    selector = "a[href*='shapely.']"  # Functions like Point
    typ = "Python API"
    tools = fetch_and_parse(url, selector)
    for t in tools:
        t["type"] = typ
        t["domain"] = "Geometry"
    return tools

def fetch_fiona():
    url = "https://fiona.readthedocs.io/en/latest/fiona.html"
    selector = "a[href*='fiona.']"  # Functions like open
    typ = "Python API"
    tools = fetch_and_parse(url, selector)
    for t in tools:
        t["type"] = typ
        t["domain"] = "Vector"
    return tools

def fetch_pyproj():
    url = "https://pyproj4.github.io/pyproj/stable/api/index.html"
    selector = "a[href*='pyproj.']"  # Functions like Transformer
    typ = "Python API"
    tools = fetch_and_parse(url, selector)
    for t in tools:
        t["type"] = typ
        t["domain"] = "Projection"
    return tools

def fetch_postgis():
    url = "https://postgis.net/docs/reference.html"
    selector = "a[href*='ST_']"  # Functions like ST_Intersects
    typ = "PostGIS Function"
    tools = fetch_and_parse(url, selector)
    for t in tools:
        t["type"] = typ
        t["domain"] = "Spatial SQL"
    return tools

# Main pipeline
def run_pipeline(append_existing=True):
    from gepro import run_cleaning_pipeline
    all_chunks = []
    
    # Fetch from each source (add delays to be polite)
    sources = [
        ("GDAL", fetch_gdal),
        ("GRASS", fetch_grass),
        ("QGIS", fetch_qgis),
        ("SAGA", fetch_saga),
        ("GeoPandas", fetch_geopandas),
        ("Rasterio", fetch_rasterio),
        ("Shapely", fetch_shapely),
        ("Fiona", fetch_fiona),
        ("PyProj", fetch_pyproj),
        ("PostGIS", fetch_postgis)
    ]
    
    for name, fetch_func in sources:
        print(f"Fetching {name} tools...")
        try:
            new_chunks = fetch_func()
            all_chunks.extend(new_chunks)
            print(f"Got {len(new_chunks)} from {name}")
        except Exception as e:
            print(f"Error fetching {name}: {e}")
        time.sleep(1)  # Rate limit
    
    # Dedupe (simple: by tool name)
    unique_chunks = {c["tool"]: c for c in all_chunks}.values()
    
    if append_existing:
        # Backup old file
        filename = "data/chunks.jsonl"
        if os.path.exists(filename):
            os.rename(filename, f"data/chunks_backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}.jsonl")
    
    save_chunks(list(unique_chunks), "data/chunks.jsonl")
    
    # Run cleaning pipeline
    print("Running cleaning pipeline...")
    run_cleaning_pipeline("data/chunks.jsonl")
    
    # Rebuild FAISS index
    print("Rebuilding FAISS index...")
    os.system("python3 build_index.py")
    print("Pipeline done! New chunks added, cleaned, and index rebuilt.")

if __name__ == "__main__":
    run_pipeline()