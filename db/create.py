"""Instructions to create the database from scratch. New functions are used to update the database"""
__author__ = 'Ayush Nag'

import warnings
import sqlite3
import pandas as pd
import pyworms
from pandas import DataFrame
from geolabel import GeoLabel

# columns expected in the sample table
sample_cols: tuple = ("latitude", "longitude", "timestamp", "front_zone", "sector", "depth", "pressure",
                      "tot_depth_water_col", "source_name", "aphia_id", "salinity", "temperature", "density",
                      "chlorophyll", "phaeopigments", "fluorescence", "primary_prod", "cruise", "down_par",
                      "light_intensity", "light_transmission", "mld", "scientific_name", "prasinophytes",
                      "cryptophytes", "mixed_flagellates", "diatoms", "haptophytes", "nitrate", "nitrite", "pco2",
                      "diss_oxygen", "diss_inorg_carbon", "diss_inorg_nitrogen", "diss_inorg_phosp", "diss_org_carbon",
                      "diss_org_nitrogen", "part_org_carbon", "part_org_nitrogen", "org_carbon", "org_matter",
                      "org_nitrogen", "phosphate", "silicate", "tot_nitrogen", "tot_part_carbon", "tot_phosp", "ph",
                      "origin_id", "strain", "notes")

# columns expected in the occurence table
occurrence_cols: tuple = ("latitude", "longitude", "timestamp", "aphia_id", "front_zone", "sector", "depth", "notes")

# columns expected in the taxonomy table
taxa_cols: tuple = ("aphia_id", "scientific_name", "superkingdom", "kingdom", "phylum", "subphylum", "superclass",
                    "class", "subclass", "superorder", "t_order", "suborder", "infraorder", "superfamily",
                    "family", "genus", "species", "modified")

# worms output -> sql col name. Also include columns from the original data that are needed but don't need renaming
# Ex: "class" -> "class" means col name is correct but class column is needed for calculations and/or used in database
worms_sql: dict = {"AphiaID": "aphia_id", "scientificname": "scientific_name", "superkingdom": "superkingdom",
                   "kingdom": "kingdom", "phylum": "phylum", "subphylum": "subphylum", "superclass": "superclass",
                   "class": "class", "subclass": "subclass", "superorder": "superorder", "order": "t_order",
                   "suborder": "suborder", "infraorder": "infraorder", "superfamily": "superfamily",
                   "family": "family", "genus": "genus", "species": "species", "modified": "modified"}

# lter -> sql col name. Also include columns from the original data that are needed but don't need renaming
lter_sql: dict = {"DatetimeGMT": "timestamp", "Latitude": "latitude", "Longitude": "longitude",
                  "Depth": "depth", "Temperature": "temperature", "Salinity": "salinity", "Density": "density",
                  "Chlorophyll": "chlorophyll", "Fluorescence": "fluorescence", "Phaeopigment": "phaeopigments",
                  "PrimaryProduction": "primary_prod", "studyName": "cruise", "PAR": "down_par",
                  "Prasinophytes": "prasinophytes", "Cryptophytes": "cryptophytes",
                  "MixedFlagellates": "mixed_flagellates", "Diatoms": "diatoms", "Haptophytes": "haptophytes",
                  "NO3": "nitrate", "NO2": "nitrite", "DIC1": "diss_inorg_carbon", "DOC": "diss_org_carbon",
                  "POC": "part_org_carbon", "SiO4": "silicate", "N": "tot_nitrogen",
                  "PO4": "phosphate", "Notes1": "notes"}

# phytobase -> sql col name. Also include columns from the original data that are needed but don't need renaming
phybase_sql: dict = {"scientificName": "scientific_name", "decimalLongitude": "longitude",
                     "decimalLatitude": "latitude", "year": "year", "month": "month", "day": "day",
                     "depth": "depth"}


def write_lter() -> None:
    """Writes LTER dataset to database"""
    sample_df: DataFrame = pd.read_csv('../data/datasets/lter.csv', encoding='unicode_escape')
    sample_df = clean_df(sample_df, lter_sql)

    # drop rows with null time, lat, or long
    sample_df = sample_df.dropna(subset=['timestamp', 'longitude', 'latitude'])

    sample_df = GeoLabel.label_zones(sample_df, 'longitude', 'latitude').drop('index_right', axis=1)
    sample_df = GeoLabel.label_sectors(sample_df, 'latitude')

    # write sample dataframe to sql database
    write_df_sql("sample", sample_df, sample_cols)


def write_phybase() -> None:
    """Writes Phytobase dataset to database"""
    occ_df: DataFrame = pd.read_csv('../data/datasets/phytobase.csv', encoding='unicode_escape')
    occ_df = clean_df(occ_df, phybase_sql)

    sci_names_data = set(occ_df['scientific_name'].unique())
    sci_names_micro = set(cur.execute("select scientific_name from taxonomy").fetchall())
    missing: set = sci_names_data - sci_names_micro  # sci_names that are missing from our database taxa records
    # get full taxonomy of microscopy data as dataframe
    # TODO: enable this line when not testing; taxa_df: DataFrame = worms_taxa(list(missing))
    taxa_df: DataFrame = clean_df(pd.read_csv('../data/datasets/micro_phybase.csv'), worms_sql)  # Testing only

    # keep only data in the Southern Ocean (latitude < -30 degrees)
    # not filtered earlier to get maximum taxa data possible for microscopy table
    occ_df = occ_df[occ_df['latitude'] < -30]
    # drop rows with null time, lat, or long
    occ_df = occ_df.dropna(subset=['longitude', 'latitude'])
    # merge three columns into one with proper datetime format (no NaT)
    occ_df['timestamp'] = pd.to_datetime(occ_df[['year', 'month', 'day']], format='%m-%d-%Y',
                                         errors='coerce').dropna()
    occ_df = occ_df.drop(columns=['year', 'month', 'day'])
    # join on sample and taxonomy (by aphia_id), only keep cols in the occurrence table (filter out order, genus, etc)
    occ_df: DataFrame = pd.merge(occ_df, taxa_df).filter(occurrence_cols)

    occ_df = GeoLabel.label_zones(occ_df, 'longitude', 'latitude').drop('index_right', axis=1)
    occ_df = GeoLabel.label_sectors(occ_df, 'latitude')

    # write taxonomy dataframe to sql database
    write_df_sql("taxonomy", taxa_df, taxa_cols)
    # write occurrence dataframe to sql database
    write_df_sql("occurrence", occ_df, occurrence_cols)


def write_df_sql(table_name: str, data: DataFrame, cols: tuple) -> None:
    """Writes data frame to the SQLite table table_name:param"""
    assert set(data.columns.values.tolist()).issubset(set(cols)), f'Provided {table_name} table has invalid column(s)'
    # Create temp table, send data to table_name, and drop temp table
    data.to_sql("temp", con=con, index=False)
    cols_str: str = csl(data.columns.values.tolist())
    cur.execute(f"insert into {table_name} ({cols_str}) select {cols_str} from temp")
    cur.execute(f"drop table temp")
    con.commit()


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
    return clean_df(pd.DataFrame(microscopy), worms_sql)


def clean_df(data: DataFrame, df_sql_map: dict) -> DataFrame:
    """Performs few operations on DF for ease of use and prepare for inserting into SQLite table"""
    data = data.filter(df_sql_map.keys())  # filter out columns that are not in the set
    return data.rename(columns=df_sql_map)  # rename columns using dict()


def csl(cols: list) -> str:
    """Converts list of values to comma separated string. Ex: [A, B, C] --> A, B, C"""
    return ', '.join(cols)


con = sqlite3.connect("sophy.db")
cur = con.cursor()

with open('create_tables.sql', 'r') as create_tables:
    con.executescript(create_tables.read())
con.commit()

write_lter()
write_phybase()

con.close()  # closes connection
print('DONE')
