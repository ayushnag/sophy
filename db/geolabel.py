__author__ = 'Ayush Nag'

from os.path import exists
import numpy as np
import pandas as pd
import scipy.io as sio
import cartopy
import cartopy.crs as ccrs
import matplotlib as plt
import geopandas as gpd
import alphashape
import pyproj
from shapely.geometry import Polygon
from shapely.ops import transform


class GeoLabel:
    """Defines static methods that can be used to interact with Southern Ocean fronts and sectors"""
    kim_orsi_file: str = '../data/fronts/ys_fronts.mat'
    gray_fronts_file: str = '../data/fronts/fronts_Gray.mat'
    fronts_shapefile: str = '../data/shapefiles/fronts/so_fronts.shp'
    zones_shapefile: str = '../data/shapefiles/zones/so_zones.shp'

    @staticmethod
    def create_fronts_zones_shapes():
        """Creates shapefiles for fronts and zones between fronts"""
        shapes: dict = {}
        world: gpd.GeoDataFrame = gpd.read_file(gpd.datasets.get_path("naturalearth_lowres"))
        world = world.to_crs(epsg=3031)
        antarctica: Polygon = world[world['continent'] == 'Antarctica']['geometry'].values[0]
        south_america: Polygon = world[world['continent'] == 'South America']['geometry'].values[0]
        project = pyproj.Transformer.from_crs(pyproj.CRS('EPSG:4326'), pyproj.CRS('EPSG:3031'),
                                              always_xy=True).transform

        gray_mat: dict = sio.loadmat(GeoLabel.gray_fronts_file)
        stf: Polygon = transform(project, Polygon(zip(gray_mat['lon_stf'][0], gray_mat['lat_stf'][0])))
        shapes['STF'] = stf - south_america

        # Writes the Kim & Orsi 2014 fronts to a shapefile
        orsi_mat: dict = sio.loadmat('../data/fronts/ys_fronts.mat')
        # fronts = ([[lat1, lon1], [lat2, lon2]], [[lat1, lon1], ...], ...)
        orsi_fronts: tuple = orsi_mat['ys_fronts'].tolist()[0][0]
        # filters out extra data and only keeps the 4 Southern Ocean fronts
        orsi_fronts = orsi_fronts[:3]
        front_names: tuple = ('SAF', 'PF', 'SACC')
        # points from each front that follow a smooth contour (no holes in the front)
        keep: tuple = ((44, 2633), (0, 2305), (0, 2614))
        for i, orsi_front in enumerate(orsi_fronts):
            # convert np array to df
            front_df = pd.DataFrame(data=orsi_front, columns=['Latitude', 'Longitude'],
                                    index=np.arange(len(orsi_front)))
            # remove extra points such as small holes in the front
            front_df = front_df.iloc[keep[i][0]:keep[i][1]]
            # data has points [-180, 360] but [-180, 180] is duplicate of [0, 360]
            front_df = front_df[front_df.Latitude <= 180]
            # make new polygon and add to list
            orsi_shp: Polygon = transform(project, Polygon(zip(front_df.Latitude, front_df.Longitude)))
            shapes[front_names[i]] = orsi_shp

        ice = np.fromfile("../data/sea_ice/mean.sep.1979-2021.s", dtype=np.uint8)
        dx = dy = 25000
        x = np.arange(-3950000, +3950000, +dx)
        y = np.arange(+4350000, -3950000, -dy)
        grid = np.dstack(np.meshgrid(x, y)).reshape(-1, 2)
        points = grid[np.logical_and(15 <= ice, ice <= 25)].T
        sie_gdf = gpd.GeoDataFrame(geometry=gpd.points_from_xy(x=points[0], y=points[1]), crs='EPSG:3031')
        # Generating alpha shape takes ~8 minutes
        alpha: gpd.GeoDataFrame = alphashape.alphashape(sie_gdf)
        sie: Polygon = alpha['geometry'].values[0]
        shapes['SIE'] = sie

        fronts_gdf = gpd.GeoDataFrame({'front': shapes.keys(), 'geometry': shapes.values()}, crs='EPSG:3031')
        fronts_gdf.to_file(GeoLabel.fronts_shapefile)

        zones: dict = {'zone': ['SAZ', 'PFZ', 'ASZ', 'SOZ', 'SIZ'], 'geometry': [shapes['STF'] - shapes['SAF'],
                                                                                 shapes['SAF'] - shapes['PF'],
                                                                                 shapes['PF'] - shapes['SACC'],
                                                                                 shapes['SACC'] - shapes['SIE'],
                                                                                 shapes['SIE'] - antarctica]}
        zones_gdf = gpd.GeoDataFrame(zones, crs='EPSG:3031')
        zones_gdf.to_file(GeoLabel.zones_shapefile)

    @staticmethod
    def get_zone(lat: float, lon: float) -> str:
        assert lat <= -30, "Provided latitude is not in the Southern Ocean (must be less than -30 degrees)"
        # Calls label_fronts with lat, lon pair as DataFrame
        return GeoLabel.label_zones(pd.DataFrame([(lat, lon)], columns=['lat', 'lon']), 'lat', 'lon')['zone'][0]

    @staticmethod
    def label_zones(data: pd.DataFrame, lat_col: str, lon_col: str) -> pd.DataFrame:
        """Labels provided data with fronts"""
        assert {lat_col, lon_col}.issubset(
            data.columns), f'"{lat_col}" or "{lon_col}"are not present in the provided DataFrame'
        assert exists(
            GeoLabel.zones_shapefile), 'missing frontal zones shapefile; try running create_fronts_zones_shapes()'

        data_gdf = gpd.GeoDataFrame(data, geometry=gpd.points_from_xy(data[lat_col], data[lon_col]), crs='EPSG:4326')
        data_gdf.to_crs(crs='EPSG:3031', inplace=True)

        zones_gdf = gpd.read_file(GeoLabel.zones_shapefile)

        result = gpd.sjoin(data_gdf, zones_gdf)
        return pd.DataFrame(result.drop(columns='geometry'))

    @staticmethod
    def get_sector(lat: float, lon: float) -> str:
        assert lat <= -30, "Provided latitude is not in the Southern Ocean (must be less than -30 degrees)"
        # Calls label_fronts with lat, lon pair as DataFrame
        return GeoLabel.label_sectors(pd.DataFrame([(lat, lon)], columns=['lat', 'lon']), 'lat', 'lon')['sector'][0]

    @staticmethod
    def label_sectors(data: pd.DataFrame, lat_col: str, lon_col: str) -> pd.DataFrame:
        """Labels provided data with sectors"""
        # So the way Im going to do this is with lines of longitude
        # so if it's x then do blah
        print('temp')

    @staticmethod
    def plot_orsi_fronts():
        """Plots the contents of ys_fronts.mat on a Southern Ocean map"""
        map_proj = ccrs.SouthPolarStereo()
        fig = plt.figure(figsize=[20, 20])  # inches
        ax = plt.subplot(projection=map_proj)
        ax.set_extent([-180, 180, -90, -39.4], ccrs.PlateCarree())
        fig.subplots_adjust(bottom=0.05, top=0.95, left=0.04, right=0.95, wspace=0.02)

        ax.add_feature(cartopy.feature.LAND)
        ax.add_feature(cartopy.feature.COASTLINE)
        ax.gridlines(draw_labels=True)

        mat_data: dict = sio.loadmat(GeoLabel.kim_orsi_file)
        # mat_data = ([[lat1, lon1], [lat2, lon2]], [[lat1, lon1], ...], ...)
        orsi_fronts: tuple = mat_data['ys_fronts'].tolist()[0][0]
        # filters out extra data and only keeps the 4 Southern Ocean fronts
        orsi_fronts = orsi_fronts[:4]
        colors = ['c', 'b', 'g', 'r']
        for i, orsi_front in enumerate(orsi_fronts):
            front = orsi_front.T
            # data has points [-180, 360] but [-180, 180] is duplicate of [0, 360]
            extra = np.where(front[0] > 180)
            # delete [180, 360]
            lat, lon = np.delete(front[0], extra), np.delete(front[1], extra)
            # remove NaN's
            lat, lon = lat[~np.isnan(lat)], lon[~np.isnan(lon)]
            ax.plot(lat, lon, marker='o', linestyle='', color=colors[i], transform=ccrs.PlateCarree())
        plt.show()
