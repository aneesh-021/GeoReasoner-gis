import geopandas as gpd
from shapely.geometry import LineString, Polygon
import os

os.makedirs('data/input', exist_ok=True)

# Create major_rivers
rivers = gpd.GeoDataFrame({
    'name': ['Mississippi', 'Ohio'],
    'geometry': [LineString([(0, 0), (10, 10)]), LineString([(0, 10), (10, 0)])]
}, crs="EPSG:3857")
rivers.to_file('data/input/major_rivers.shp')

# Create urban_zoning
zoning = gpd.GeoDataFrame({
    'zone': ['Residential', 'Industrial'],
    'geometry': [Polygon([(2, 2), (2, 8), (8, 8), (8, 2)]), Polygon([(0, 0), (0, 2), (2, 2), (2, 0)])]
}, crs="EPSG:3857")
zoning.to_file('data/input/urban_zoning.shp')

print("Created major_rivers.shp and urban_zoning.shp in data/input/")
