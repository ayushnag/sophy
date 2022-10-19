"""Instructions to create the database from scratch. New functions are used to update the database"""
__author__ = 'Ayush Nag'

import warnings
import sqlite3
import pandas as pd
import pyworms
import geolabel
import sophysql
from pandas import DataFrame


con = sqlite3.connect("sophy.db")
cur = con.cursor()
sophysql.create_tables()

sample_cols: tuple = sophysql.get_table_cols("sample")
occurrence_cols: tuple = sophysql.get_table_cols("occurrence")
taxa_cols: tuple = sophysql.get_table_cols("taxonomy")


def write_lter() -> None:
    """Writes LTER dataset to database"""
    sample_df: DataFrame = pd.read_csv('../data/datasets/lter.csv', encoding='unicode_escape')

    # drop rows with null time, lat, or long
    sample_df = sample_df.dropna(subset=['timestamp', 'longitude', 'latitude'])

    sample_df = geolabel.label_zones(sample_df, 'longitude', 'latitude').drop('index_right', axis=1)
    sample_df = geolabel.label_sectors(sample_df, 'longitude')

    # TODO: chemtax into groups
    # make a function that can take in a dataframe with some* chemtax cols and return the same DF with the group_X cols filled out
    # write sample dataframe to sql database
    sophysql.write_dataset(data=sample_df, table_name="sample")




def microscopy_to_groups(micro_df: DataFrame) -> DataFrame:
    x: int = 8
    # first create column that gives them their label to be able to be merged
    # all other == other
    # so first


def write_phybase() -> None:
    """Writes Phytobase dataset to database"""
    occ_df: DataFrame = pd.read_csv('../data/datasets/phytobase.csv', encoding='unicode_escape')

    sci_names_data = set(occ_df['scientific_name'].unique())
    sci_names_micro = set(cur.execute("select scientific_name from taxonomy").fetchall())
    missing: set = sci_names_data - sci_names_micro  # sci_names that are missing from our database taxa records
    # get full taxonomy of microscopy data as dataframe
    taxa_df: DataFrame = pd.read_csv('../data/datasets/sample_worms.csv')  # Testing only
    taxa_df = taxa_df.rename(columns=worms_sql)
    # not filtered earlier to get maximum taxa data possible for microscopy table
    occ_df = basic_filter(occ_df)
    # merge three columns into one with proper datetime format (no NaT)
    occ_df['timestamp'] = pd.to_datetime(occ_df[['year', 'month', 'day']], format='%m-%d-%Y',
                                         errors='coerce').dropna()
    occ_df = occ_df.drop(columns=['year', 'month', 'day'])
    # join on sample and taxonomy (by aphia_id), only keep cols in the occurrence table (filter out order, genus, etc)
    occ_df: DataFrame = pd.merge(occ_df, taxa_df).filter(occurrence_cols)

    occ_df = geolabel.label_zones(occ_df, 'longitude', 'latitude').drop('index_right', axis=1)
    occ_df = geolabel.label_sectors(occ_df, 'longitude')

    # write taxonomy dataframe to sql database
    sophysql.write_dataset(data=taxa_df, table_name="taxonomy")
    # write occurrence dataframe to sql database
    sophysql.write_dataset(data=occ_df, table_name="occurrence")


def write_joy_warren() -> None:
    """Writes Joy-Warren 2019 dataset to database"""
    sample_df: DataFrame = pd.read_csv('../data/datasets/joy_warren.csv', encoding='unicode_escape')
    sample_df = basic_filter(sample_df)

    # shifts index to match the id in the sample table
    max_id: int = sophysql.query("select max(id) from sample")[0][0]
    sample_df.index += (max_id + 1)

    # TODO: chemtax into categories

    sample_df = geolabel.label_zones(sample_df, 'longitude', 'latitude').drop('index_right', axis=1)
    sample_df = geolabel.label_sectors(sample_df, 'longitude')


def write_alderkamp() -> None:
    """Writes Alderkamp 2019 dataset to database"""
    sample_df: DataFrame = pd.read_csv('../data/datasets/alderkamp.csv', encoding='unicode_escape')
    sample_df = basic_filter(sample_df)
    # label zones and sectors
    sample_df = geolabel.label_zones(sample_df, 'longitude', 'latitude').drop('index_right', axis=1)
    sample_df = geolabel.label_sectors(sample_df, 'longitude')
    sophysql.write_dataset(data=sample_df, table_name="sample")


def basic_filter(data: DataFrame) -> DataFrame:
    """Performs basic fixes on DF before inserting into SQLite table"""
    # keep only data in the Southern Ocean (latitude <= -30 degrees)
    data = data[data['latitude'] <= -30]
    data = data.dropna(subset=['longitude', 'latitude'])
    return data


def csl(cols: list) -> str:
    """Converts list of values to comma separated string. Ex: [A, B, C] --> A, B, C"""
    return ', '.join(cols)


write_lter()
write_phybase()

con.close()  # closes connection
print('DONE')
