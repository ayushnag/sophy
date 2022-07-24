# This file will define several static methods that can be used to interact with fronts
# TODO: Add DOI and URL to paper + data source
import scipy.io as sio
from shapely.geometry import Polygon
from shapely.geometry import Point
import matplotlib.pyplot as plt
import pandas as pd
import geopandas as gpd
from pandas import DataFrame
from os.path import exists



def read_shapefile(path: str) -> gpd.GeoDataFrame:
    if not exists(Fronts.fronts_file):
        Fronts.kim_orsi_to_shapefile()
    elif not exists(Fronts.zones_file):
        Fronts.fronts_to_zones()
    return gpd.read_file(path)

class Fronts:
    kim_orsi_file = "../data/fronts/ys_fronts.mat"
    fronts_file = "../data/fronts/so_fronts.shp"
    zones_file = "../data/fronts/so_zones.shp"
    front_shapes: gpd.GeoDataFrame = read_shapefile(fronts_file)
    zones_shapes: gpd.GeoDataFrame = read_shapefile(zones_file)

    # Writes the Kim & Orsi 2014 fronts to a shapefile
    def kim_orsi_to_shapefile(self):
        kim_orsi: dict = sio.loadmat(self.kim_orsi_file)
        # fronts = ([[lat1, lon1], [lat2, lon2]], [[lat1, lon1], ...], ...)
        orsi_fronts: tuple = kim_orsi['ys_fronts'].tolist()[0][0]
        # filters out extra data and only keeps the 4 Southern Ocean fronts
        orsi_fronts = orsi_fronts[:4]
        for i in range(len(orsi_fronts)):
            # write shapely file
            front = orsi_fronts[i].tolist()
            front.pop(0)
            front1 = Polygon(front)

    # Creates zones between Southern Ocean fronts. Also includes Sea-Ice Extent
    # TODO: Do I need Anartica's shape to make the SIE? Need the difference() between two shapes
    def fronts_to_zones(self):
        for index, poi in self.front_shapes.iterrows():
            # shape.difference(other shape) to get the zone
        # assert that the two files were made properly

    # Reads shapefile and returns tuple of Polygons
    def find(self, lat: float, lon: float) -> str:
        # assert that range is a valid lat lon
        # assert that the range is in the Southern Ocean
        point = Point(lat, lon)
        for front in self.front_shapes:
            if point.within(front):
                return front.to_string

    def label_points(self, data: DataFrame) -> DataFrame:
        # need a loop to do the difference of the shapes
        return gpd.tools.sjoin(data, fronts_gdf, predicate="with", how='left')

# I need to make a script that does what exactly
# Takes in a [(x, y), (x, y)] of coordinates
# Then convert them to a shapefile
# Read into the separate script or function
# Write simple function that takes in a point or several points and locates which frontal zone its in
# So we need to fix the schema to take this into account
