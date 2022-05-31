import warnings
import sqlite3
import pandas as pd
import pyworms
from pandas import DataFrame

# columns expected in the sample table
sample_cols: tuple = ("latitude", "longitude", "timestamp", "depth", "pressure", "tot_depth_water_col", "source_name",
                      "aphia_id", "region", "salinity", "temperature", "density", "chlorophyll", "phaeopigments",
                      "fluorescence", "primary_prod", "cruise", "down_par", "light_intensity", "scientific_name",
                      "prasinophytes", "cryptophytes", "mixed_flagellates", "diatoms", "haptophytes", "nitrate",
                      "nitrite", "pco2", "diss_oxygen", "diss_inorg_carbon", "diss_inorg_nitrogen", "diss_inorg_phosp",
                      "diss_org_carbon", "diss_org_nitrogen", "part_org_carbon", "part_org_nitrogen", "org_carbon",
                      "org_matter", "org_nitrogen", "phosphate", "silicate", "tot_nitrogen", "tot_part_carbon",
                      "tot_phosp", "ph", "origin_id", "strain", "notes")

# columns expected in the microscopy table
microscopy_cols: tuple = ("aphia_id", "scientific_name", "superkingdom", "kingdom", "phylum", "subphylum", "superclass",
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
                     "depth": "depth", "organismQuantity": "organismQuantity"}


def write_lter():
    # read and clean dataset
    sample_df: DataFrame = pd.read_csv('datasets/lter.csv', encoding='unicode_escape')
    sample_df = clean_df(sample_df, lter_sql)

    # drop rows with null time, lat, or long
    sample_df.dropna(subset=['timestamp', 'latitude', 'longitude'], inplace=True)

    # write sample dataframe to sql database
    assert set(sample_df.columns.values.tolist()).issubset(set(sample_cols)), "Created sample table has invalid column(s)"
    cols_str: str = csl(sample_df)
    sample_df.to_sql('temp_lter', con=con, index=False)
    cur.execute(f"insert into sample ({cols_str}) select {cols_str} from temp_lter")
    cur.execute("drop table temp_lter")
    con.commit()


def write_phybase():
    # read and clean dataset
    sample_df: DataFrame = pd.read_csv('datasets/phytobase.csv', encoding='unicode_escape')
    sample_df = clean_df(sample_df, phybase_sql)

    # Merge three columns into one with proper datetime format (no NaT)
    sample_df['timestamp'] = pd.to_datetime(sample_df[['year', 'month', 'day']], format='%m-%d-%Y', errors='coerce').dropna()
    sample_df.drop(columns=['organismQuantity', 'year', 'month', 'day'], inplace=True)

    sci_names_data = set(sample_df['scientific_name'].unique())
    sci_names_micro = set(cur.execute("select scientific_name from microscopy").fetchall())
    missing: set = sci_names_data - sci_names_micro  # sci_names that are missing from our database taxa records
    # get full taxonomy of microscopy data as dataframe
    # micro_df: DataFrame = worms_taxa(list(missing)) ~7 minutes for 1700 taxa from phytobase
    micro_df: DataFrame = clean_df(pd.read_csv('datasets/micro_phybase.csv'), worms_sql)  # Only for testing purposes
    # join on sample and microscopy (by aphia_id), only keep cols in the sample table (filter out order, genus, etc)
    sample_df: DataFrame = pd.merge(sample_df, micro_df).filter(sample_cols)

    # write microscopy dataframe to sql database
    assert set(micro_df.columns.values.tolist()).issubset(set(microscopy_cols)), "Created microscopy table has invalid column(s)"
    cols_str: str = csl(micro_df)
    micro_df.to_sql("temp_micro", con=con, index=False)
    cur.execute(f"insert into microscopy ({cols_str}) select {cols_str} from temp_micro")
    cur.execute("drop table temp_micro")
    con.commit()

    # write sample dataframe to sql database
    assert set(sample_df.columns.values.tolist()).issubset(set(sample_cols)), "Created sample table has invalid column(s)"
    sample_df.to_sql("temp_phybase", con=con, index=False)
    cols_str: str = csl(sample_df)
    cur.execute(f"insert into sample ({cols_str}) select {cols_str} from temp_phybase")
    cur.execute("drop table temp_phybase")
    con.commit()


# Gets full taxonomy records of given scientific names using the WoRMS database
# Note: param: taxa ordering does not matter however WoRMS API requires list instead of set
def worms_taxa(taxa: list) -> DataFrame:
    microscopy, no_result = list()
    # full taxa records from WoRMS; worms = [[{}], [{}], [], [{}], ...]
    worms: list = pyworms.aphiaRecordsByMatchNames(taxa)
    for i in range(len(worms)):
        if len(worms[i]) > 0:
            microscopy.append(worms[i][0])
        else:  # no WoRMS record was found since len(result) = 0
            no_result.append(taxa[i])
    if len(no_result) != 0:  # outputs taxa (first 20 for brevity) where WoRMS database found no result
        warnings.warn(f"No results found by WoRMS database: {str(no_result[:20])}...")
    # convert list of dict() -> dataframe and clean it
    return clean_df(pd.DataFrame(microscopy), worms_sql)


# Performs few operations on DF for ease of use prepare for inserting into SQLite table
def clean_df(df: DataFrame, source_sql: dict) -> DataFrame:
    df = df.filter(source_sql.keys())  # filter out columns that are not in the set
    return df.rename(columns=source_sql)  # rename columns using dict()


# Returns comma seperated list of DataFrame columns
# Ex: [A, B, C] --> A, B, C
def csl(df: DataFrame) -> str:
    return ', '.join(df.columns.values.tolist())


con = sqlite3.connect("species_test.db")
cur = con.cursor()

with open('create_tables.sql', 'r') as create_tables:
    con.executescript(create_tables.read())
write_lter()
write_phybase()

con.close()  # closes connection
