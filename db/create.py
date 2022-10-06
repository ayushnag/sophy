"""Instructions to create the database from scratch. New functions are used to update the database"""
__author__ = 'Ayush Nag'

import warnings
import sqlite3
import pandas as pd
import pyworms
import geolabel
import sophysql
from pandas import DataFrame

# worms output -> sql col name. Also include columns from the original data that are needed but don't need renaming
# Ex: "class" -> "class" means col name is correct but class column is needed for calculations and/or used in database
worms_sql: dict = {"AphiaID": "aphia_id", "scientificname": "scientific_name", "superkingdom": "superkingdom",
                   "kingdom": "kingdom", "phylum": "phylum", "subphylum": "subphylum", "superclass": "superclass",
                   "class": "class", "subclass": "subclass", "superorder": "superorder", "order": "t_order",
                   "suborder": "suborder", "infraorder": "infraorder", "superfamily": "superfamily",
                   "family": "family", "genus": "genus", "species": "species", "modified": "modified"}

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
    # write sample dataframe to sql database
    sophysql.write_dataset("sample", sample_df)


def write_phybase() -> None:
    """Writes Phytobase dataset to database"""
    occ_df: DataFrame = pd.read_csv('../data/datasets/phytobase.csv', encoding='unicode_escape')

    sci_names_data = set(occ_df['scientific_name'].unique())
    sci_names_micro = set(cur.execute("select scientific_name from taxonomy").fetchall())
    missing: set = sci_names_data - sci_names_micro  # sci_names that are missing from our database taxa records
    # get full taxonomy of microscopy data as dataframe
    # TODO: enable this line when not testing; taxa_df: DataFrame = worms_taxa(list(missing))
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
    sophysql.write_dataset(table_name="taxonomy", data=taxa_df)
    # write occurrence dataframe to sql database
    sophysql.write_dataset(table_name="occurrence", data=occ_df)


def write_joy_warren() -> None:
    """Writes Joy-Warren 2019 dataset to database"""
    sample_df: DataFrame = pd.read_csv('../data/datasets/joy_warren.csv', encoding='unicode_escape')
    sample_df = basic_filter(sample_df)
    sample_df = geolabel.label_zones(sample_df, 'longitude', 'latitude').drop('index_right', axis=1)
    sample_df = geolabel.label_sectors(sample_df, 'longitude')
    # add entries from supplemental csv into the microscopy table
    # TODO: chemtax into groups


def write_alderkamp() -> None:
    """Writes Alderkamp 2018 dataset to database"""
    sample_df: DataFrame = pd.read_csv('../data/datasets/alderkamp.csv', encoding='unicode_escape')
    sample_df = basic_filter(sample_df)
    # label zones and sectors
    sample_df = geolabel.label_zones(sample_df, 'longitude', 'latitude').drop('index_right', axis=1)
    sample_df = geolabel.label_sectors(sample_df, 'longitude')
    sophysql.write_dataset("sample", sample_df)


def worms_taxa(taxa: list) -> DataFrame:
    """Finds full species composition of provided taxa. Uses WoRMS database to find data"""
    microscopy, no_result = [], []
    # full taxa records from WoRMS; worms = [[{}], [{}], [], [{}], ...]
    worms: list = pyworms.aphiaRecordsByMatchNames(taxa)
    for i, taxonomy in enumerate(worms):
        if len(taxonomy) > 0:
            microscopy.append(taxonomy)
        else:  # no WoRMS record was found since len(result) = 0
            no_result.append(taxa[i])
    if len(no_result) != 0:  # outputs taxa (first 20) where WoRMS database found no result
        warnings.warn(f"No results found by WoRMS database: {str(no_result[:20])}...")
    # convert list of dict() -> dataframe and clean it
    return DataFrame(microscopy).rename(worms_sql)


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
