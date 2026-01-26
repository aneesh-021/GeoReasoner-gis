# create_test_data.py
import geopandas as gpd
from shapely.geometry import Point, Polygon
import os

# Create data/input directory if not exists
os.makedirs("data/input", exist_ok=True)
os.makedirs("output", exist_ok=True)

# Create a dummy shapefile (Farms)
data = {
    'name': ['Farm A', 'Farm B', 'Farm C'],
    'geometry': [
        Polygon([(0, 0), (0, 10), (10, 10), (10, 0)]),
        Polygon([(20, 20), (20, 30), (30, 30), (30, 20)]),
        Polygon([(40, 40), (40, 50), (50, 50), (50, 40)])
    ]
}
gdf = gpd.GeoDataFrame(data, crs="EPSG:4326")
gdf.to_file("data/input/farms.shp")

# Create a dummy shapefile (Major Rivers) - Lines
rivers_data = {
    'name': ['River A', 'River B'],
    'geometry': [
        Polygon([(0, 0), (1, 1), (2, 2)]).boundary, # Using boundary of polygon to get lines quickly or just use specific LineStrings if importing
        Polygon([(10, 10), (11, 11), (12, 12)]).boundary    
    ]
}
# Properly use LineString
from shapely.geometry import LineString
rivers_data = {
    'name': ['River Deep', 'River Wide'],
    'geometry': [
        LineString([(0, 0), (0, 50)]),
        LineString([(50, 0), (50, 50)])
    ]
}
gdf_rivers = gpd.GeoDataFrame(rivers_data, crs="EPSG:4326")
gdf_rivers.to_file("data/input/major_rivers.shp")

# Create a dummy shapefile (Urban Zoning) - Polygons
zoning_data = {
    'zone': ['Residential', 'Commercial', 'Residential', 'Industrial'],
    'geometry': [
        Polygon([(-10, -10), (-10, 60), (5, 60), (5, -10)]), # Overlaps with river at 0,0-0,50
        Polygon([(5, -10), (5, 60), (20, 60), (20, -10)]),
        Polygon([(20, -10), (20, 60), (35, 60), (35, -10)]),
        Polygon([(35, -10), (35, 60), (60, 60), (60, -10)])
    ]
}
gdf_zoning = gpd.GeoDataFrame(zoning_data, crs="EPSG:4326")
gdf_zoning.to_file("data/input/urban_zoning.shp")

print("✅ Created test data: farms.shp, major_rivers.shp, urban_zoning.shp")
