"""Defines static methods that can be used to interact with Southern Ocean fronts and sectors"""
__author__ = 'Ayush Nag'

import scipy.io as sio
from shapely.geometry import Point, MultiPoint
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from pandas import DataFrame
from os.path import exists
import cartopy
import cartopy.crs as ccrs


class GeoLabel:
    kim_orsi_file = "../data/fronts/ys_fronts.mat"
    fronts: dict = None
    #TODO: clarify fronts and zones
    front_names: tuple = ('STF', 'SAF', 'PF', 'SACC', 'SIE')
    front_zones: tuple = ('STZ', 'SAZ', 'PFZ', 'ASZ', 'SIZ')
    sectors: dict = None
    sector_names: tuple = ('Weddell Sea', 'Indian Ocean', 'Western Pacific Ocean', 'Ross Sea', 'Bellingshausen Sea')

    @staticmethod
    def kim_orsi_to_multipoints():
        """Creates MultiPoints representing the 2014 Kim and Orsi fronts. Also updates static class variable 'fronts'"""
        mat_data: dict = sio.loadmat("../data/fronts/ys_fronts.mat")
        # mat_data = ([[lat1, lon1], [lat2, lon2]], [[lat1, lon1], ...], ...)
        orsi_fronts: tuple = mat_data['ys_fronts'].tolist()[0][0]
        # filters out extra data and only keeps the 4 Southern Ocean fronts
        orsi_fronts = orsi_fronts[:4]
        fronts: dict = {}
        for i in range(len(orsi_fronts)):
            front = orsi_fronts[i].T
            # data has points [-180, 360] but [-180, 180] is duplicate of [0, 360]
            extra = np.where(front[0] > 180)
            # delete [180, 360]
            lat, lon = np.delete(front[0], extra), np.delete(front[1], extra)
            # remove NaN's
            lat, lon = lat[~np.isnan(lat)], lon[~np.isnan(lon)]
            # np.stack(lat, lon)
            fname: str = GeoLabel.front_names[i]
            fronts[fname].append(MultiPoint(np.stack((lat, lon), axis=-1)))
        GeoLabel.fronts = fronts

    @staticmethod
    def get_front(lat: float, lon: float) -> str:
        # assert that range is a valid lat lon
        # assert that the range is in the Southern Ocean
        print('temp')

    @staticmethod
    def label_fronts(data: DataFrame, lat_col: str, lon_col: str) -> DataFrame:
        """Labels provided data with fronts"""
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
        for i in range(len(orsi_fronts)):
            front = orsi_fronts[i].T
            # data has points [-180, 360] but [-180, 180] is duplicate of [0, 360]
            extra = np.where(front[0] > 180)
            # delete [180, 360]
            lat, lon = np.delete(front[0], extra), np.delete(front[1], extra)
            # remove NaN's
            lat, lon = lat[~np.isnan(lat)], lon[~np.isnan(lon)]
            ax.plot(lat, lon, marker='o', linestyle='', color=colors[i], transform=ccrs.PlateCarree())
        plt.show()
