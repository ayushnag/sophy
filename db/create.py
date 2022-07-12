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


def write_lter() -> None:
    # read and clean dataset
    sample_df: DataFrame = pd.read_csv('datasets/lter.csv', encoding='unicode_escape')
    sample_df = clean_df(sample_df, lter_sql)

    # drop rows with null time, lat, or long
    sample_df = sample_df.dropna(subset=['timestamp', 'latitude', 'longitude'])

    # write sample dataframe to sql database
    write_df_sql("sample", sample_df, sample_cols)


def write_phybase() -> None:
    # read and clean dataset
    sample_df: DataFrame = pd.read_csv('datasets/phytobase.csv', encoding='unicode_escape')
    sample_df = clean_df(sample_df, phybase_sql)

    # Merge three columns into one with proper datetime format (no NaT)
    sample_df['timestamp'] = pd.to_datetime(sample_df[['year', 'month', 'day']], format='%m-%d-%Y',
                                            errors='coerce').dropna()
    sample_df = sample_df.drop(columns=['organismQuantity', 'year', 'month', 'day'])

    sci_names_data = set(sample_df['scientific_name'].unique())
    sci_names_micro = set(cur.execute("select scientific_name from microscopy").fetchall())
    missing: set = sci_names_data - sci_names_micro  # sci_names that are missing from our database taxa records
    # get full taxonomy of microscopy data as dataframe
    #micro_df: DataFrame = worms_taxa(list(missing))
    micro_df: DataFrame = clean_df(pd.read_csv('datasets/micro_phybase.csv'), worms_sql)  # Only for testing purposes
    # join on sample and microscopy (by aphia_id), only keep cols in the sample table (filter out order, genus, etc)
    sample_df: DataFrame = pd.merge(sample_df, micro_df).filter(sample_cols)

    # write microscopy dataframe to sql database
    write_df_sql("microscopy", micro_df, microscopy_cols)
    # write sample dataframe to sql database
    write_df_sql("sample", sample_df, sample_cols)


# Writes data frame to the SQLite table named @param: 'table_name'
def write_df_sql(table_name: str, df: DataFrame, cols: tuple) -> None:
    assert cur.execute(f"select name from sqlite_master where type='table' and name='{{table_name}}'") == 1, f'{table_name} does not exist'
    assert set(df.columns.values.tolist()).issubset(set(cols)), f'Provided {table_name} table has invalid column(s)'
    df.to_sql("temp", con=con, index=False)
    cols_str: str = csl(df.columns.values.tolist())
    cur.execute(f"insert into {table_name} ({cols_str}) select {cols_str} from temp")
    cur.execute("drop table temp")
    con.commit()


# Gets full taxonomy records of given scientific names using the WoRMS database
# Note: @param: 'input' ordering does not matter, however pyworms requires a list instead of set
def worms_taxa(input: list) -> DataFrame:
    microscopy, no_result = [], []
    # full taxa records from WoRMS; worms = [[{}], [{}], [], [{}], ...]
    worms: list = pyworms.aphiaRecordsByMatchNames(input)
    for i in range(len(worms)):
        if len(worms[i]) > 0:
            microscopy.append(worms[i])
        else:  # no WoRMS record was found since len(result) = 0
            no_result.append(input[i])
    if len(no_result) != 0:  # outputs taxa (first 20 for brevity) where WoRMS database found no result
        warnings.warn(f"No results found by WoRMS database: {str(no_result[:20])}...")
    # convert list of dict() -> dataframe and clean it
    return clean_df(pd.DataFrame(microscopy), worms_sql)


# Performs few operations on DF for ease of use prepare for inserting into SQLite table
def clean_df(df: DataFrame, source_sql: dict) -> DataFrame:
    df = df.filter(source_sql.keys())  # filter out columns that are not in the set
    return df.rename(columns=source_sql)  # rename columns using dict()


# Converts list of values to comma separated string
# Ex: [A, B, C] --> A, B, C
def csl(cols: list) -> str:
    return ', '.join(cols)


con = sqlite3.connect("db\sophy.db")
cur = con.cursor()

with open('db/create_tables.sql', 'r') as create_tables:
    con.executescript(create_tables.read())
write_lter()
write_phybase()

con.close()  # closes connection
