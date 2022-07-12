import pandas as pd
import geojson
from pandas import DataFrame
from geojson import Point, Feature, Polygon

df_fronts = pd.read_pickle(r"C:\users\ayush nag\Downloads\data\02_intermediate\SOCCOM_bgc_argo_float_data\all_floatdata_analyzed.pkl")

def locate_subtropical_front(df: DataFrame):
    # this function takes in raw argo/float data and locates the fronts
    # it should output in GeoJSON format that gets written to a file not in this function
    # Subtropical Front (STF) = pot_temp at 100 m == 11 C
    # Subantarctic Front (SAF) = pot_temp at 400 m == 5 C
    # Polar Front (PF) = pot_temp == 2 C along the pot_temp-minimum in the upper 200 m
    print()