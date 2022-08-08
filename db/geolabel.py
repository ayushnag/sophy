__author__ = 'Ayush Nag'

from os.path import exists
import numpy as np
import pandas as pd
import scipy.io as sio
import matplotlib.pyplot as plt
import cartopy
import cartopy.crs as ccrs
import geopandas as gpd
from shapely.geometry import Polygon


class GeoLabel:
    """Defines static methods that can be used to interact with Southern Ocean fronts and sectors"""
    kim_orsi_file: str = '../data/fronts/ys_fronts.mat'
    fronts_shapefile: str = '../data/shapefiles/fronts/so_fronts.shp'
    zones_shapefile: str = '../data/shapefiles/zones/so_zones.shp'
    # TODO: still needs to be implemented
    sectors_shapefile: str = '../data/shapefiles/sectors/so_sectors.shp'
    world_shapefile: str = '../data/shapefiles/world/world.shp'

    @staticmethod
    def create_fronts_zones_shapes():
        """Creates shapefiles for fronts and zones between fronts"""
        # Writes the Kim & Orsi 2014 fronts to a shapefile
        mat_data: dict = sio.loadmat(GeoLabel.kim_orsi_file)
        # fronts = ([[lat1, lon1], [lat2, lon2]], [[lat1, lon1], ...], ...)
        orsi_data: tuple = mat_data['ys_fronts'].tolist()[0][0]
        # filters out extra data and only keeps the 4 Southern Ocean fronts
        orsi_data = orsi_data[:4]
        # points from each front that follow a smooth contour (no holes in the front)
        keep = ((44, 2633), (0, 2305), (0, 2614), (60, 2154))
        front_names: tuple = ('SAF', 'PF', 'SACC', 'SBdy')
        fronts: dict = {}
        for i, orsi_front in enumerate(orsi_data):
            # convert np array to df
            front_df = pd.DataFrame(data=orsi_front, columns=['Latitude', 'Longitude'], 
                                                     index=np.arange(len(orsi_front)))
            # remove extra points such as small holes in the front
            front_df = front_df.iloc[keep[i][0]:keep[i][1]]
            # data has points [-180, 360] but [-180, 180] is duplicate of [0, 360]
            front_df = front_df[front_df.Latitude <= 180]
            # make new polygon and add to list
            name = front_names[i]
            fronts[name] = Polygon(zip(front_df.Latitude, front_df.Longitude))

        fronts_gdf = gpd.GeoDataFrame(fronts, crs='EPSG:3031')
        fronts_gdf.to_file(GeoLabel.fronts_shapefile)

        world: gpd.GeoDataFrame = gpd.read_file(GeoLabel.world_shapefile)
        antarctica: gpd.GeoDataFrame = world[world['NAME'] == 'Antarctica']
        antarctica = antarctica.to_crs(epsg=3031)
        antarctica: Polygon = antarctica['geometry'].values[0]

        zones: dict = {'zone': ['PFZ', 'ASZ', 'SOZ', 'SIZ'], 'geometry': [fronts['SAF'] - fronts['PF'], 
                                                                        fronts['PF'] - fronts['SACC'], 
                                                                        fronts['SACC'] - fronts['SBdy'],
                                                                        fronts['SIE'] - antarctica]}
        zones_gdf = gpd.GeoDataFrame(zones, crs='EPSG:3031')
        zones_gdf.to_file(GeoLabel.zones_shapefile)

    @staticmethod
    def get_zone(lat: float, lon: float) -> str:
        # assert that the range is in the Southern Ocean
        # Calls label_fronts with lat, lon pair as DataFrame
        return GeoLabel.label_zones(pd.DataFrame([(lat, lon)], columns=['lat', 'lon']), 'lat', 'lon')['zone'][0]

    @staticmethod
    def label_zones(data: pd.DataFrame, lat_col: str, lon_col: str) -> pd.DataFrame:
        """Labels provided data with fronts"""
        assert {lat_col, lon_col}.issubset(data.columns), 'f"{lat_col}" or "{lon_col}" are not present in the provided DataFrame'
        assert exists(GeoLabel.zones_shapefile), 'missing frontal zones shapefile; try running create_fronts_zones_shapes()'

        # df = pd.read_csv("../data/datasets/lter.csv", encoding='unicode_escape')
        data_gdf = gpd.GeoDataFrame(data, geometry=gpd.points_from_xy(data[lat_col], data[lon_col]), crs='EPSG:4326')
        data_gdf.to_crs(crs='EPSG:3031', inplace=True)

        zones_gdf = gpd.read_file(GeoLabel.zones_shapefile)

        result = gpd.sjoin(data_gdf, zones_gdf)
        return pd.DataFrame(result.drop(columns='geometry'))


    @staticmethod
    def get_sector(lat: float, lon: float) -> str:
        # assert that the range is in the Southern Ocean
        print('temp')

    @staticmethod
    def label_sectors(data: pd.DataFrame, lat_col: str, lon_col: str) -> pd.DataFrame:
        """Labels provided data with sectors"""
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
