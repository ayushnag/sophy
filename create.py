import warnings
import pandas
import sqlite3
import pyworms
from pandas import DataFrame

sample_cols: tuple = ("latitude", "longitude", "timestamp", "depth", "pressure", "tot_depth_water_col", "source_name",
                      "aphia_id", "region", "salinity", "temperature", "density", "chlorophyll", "phaeopigments",
                      "fluorescence", "primary_prod", "cruise", "down_par", "light_intensity", "prasinophytes",
                      "cryptophytes", "mixed_flagellates", "diatoms", "haptophytes", "nitrate", "nitrite", "pco2",
                      "diss_oxygen", "diss_inorg_carbon", "diss_inorg_nitrogen", "diss_inorg_phosp", "diss_org_carbon",
                      "diss_org_nitrogen", "part_org_carbon", "part_org_nitrogen", "org_carbon", "org_matter",
                      "org_nitrogen", "phosphate", "silicate", "tot_nitrogen", "tot_part_carbon", "tot_phosp", "ph",
                      "origin_id", "strain", "notes")
microscopy_cols: tuple = ("aphia_id", "scientific_name, superkingdom", "kingdom", "phylum", "subphylum", "superclass",
                          "class", "subclass", "superorder", "order", "suborder", "infraorder", "superfamily",
                          "family", "genus", "species", "citation", "modified")

worms_micro: dict = {"AphiaID": "aphia_id", "scientificname": "scientific_name", "superkingdom": "superkingdom",
                     "kingdom": "kingdom", "phylum": "phylum", "subphylum": "subphylum", "superclass": "superclass",
                     "class": "class", "subclass": "subclass", "superorder": "superorder", "order": "order",
                     "suborder": "suborder", "infraorder": "infraorder", "superfamily": "superfamily",
                     "family": "family", "genus": "genus", "species": "species",
                     "citation": "citation", "modified": "modified"}

lter_sql: dict = {"datetimeGMT": "timestamp", "Phaeopigment": "phaeopigments", "PrimaryProduction": "primary_prod",
                  "studyName": "cruise", "PAR": "down_par", "MixedFlagellates": "mixed_flagellates",
                  "NO3": "nitrate", "NO2": "nitrite", "DIC1": "diss_inorg_carbon", "DOC": "diss_org_carbon",
                  "POC": "part_org_carbon", "SiO4": "silicate", "N": "tot_nitrogen",
                  "PO4": "phosphate", "Notes1": "notes"}

phybase_sql: dict = {"scientificName": "scientific_name", "decimalLongitude": "longitude",
                     "decimalLatitude": "latitude", "year": "year", "month": "month", "day": "day",
                     "depth": "depth", "organismQuantity": "organismQuantity"}


def write_lter():
    # full dataset
    sample_df: DataFrame = pandas.read_csv('datasets/lter.csv', encoding='unicode_escape')
    sample_df = clean_df(sample_df, lter_sql)

    cols_str = csl(sample_df)
    sample_df.to_sql('temp_lter', con=con, index=False)
    # Inserts all values from lter temp table into main sample table
    cur.execute(f"insert into sample ({cols_str}) select {cols_str} from temp_lter")
    cur.execute("drop table temp_lter")
    con.commit()  # save changes to .db file


def write_phybase():
    # full dataset
    sample_df: DataFrame = pandas.read_csv('datasets/phytobase.csv', encoding='unicode_escape')
    sample_df = clean_df(sample_df, phybase_sql)

    # TODO: merge day, month, year column into one col (timestamp)

    # sci_names_data = set(sample_df['scientific_name'].unique())
    # sci_names_micro = set(cur.execute("select scientific_name from microscopy").fetchall())
    # missing: set = sci_names_data - sci_names_micro
    # micro_df = calc_microscopy(missing)
    micro_df = pandas.read_csv('micro_phybase.csv')  # Only for testing purposes

    assert set(micro_df.columns.values.tolist()).issubset(set(microscopy_cols)), "Created microscopy table has invalid column(s)"

    cols_str = csl(micro_df)
    micro_df.to_sql("temp_micro", con=con, index=False)
    cur.execute(f"insert into sample ({cols_str}) select {cols_str} from temp_micro")
    cur.execute("drop table temp_micro")
    con.commit()  # save changes to .db file

    assert set(sample_df.columns.values.tolist()).issubset(set(sample_cols)), "Created sample table has invalid column(s)"

    sample_df.to_sql("temp_phybase", con=con, index=False)
    cols_str = csl(sample_df)
    cur.execute(f"insert into sample ({cols_str}) select {cols_str} from temp_phybase")
    cur.execute("drop table temp_phybase")
    con.commit()  # save changes to .db file

    # TODO: FK setup of new samples
    # Why dont we do it on the new temp table?
    # Create it then do the FK thing


def calc_microscopy(new_taxa: set) -> DataFrame:
    new_micro = dict()
    for taxa in new_taxa:
        result = pyworms.aphiaRecordsByMatchNames(taxa)[0]
        if len(result) > 0:
            new_micro[taxa] = result[0]
        else:
            warnings.warn(f"No WoRMS result was found for: {taxa}")
    return clean_df(pandas.DataFrame.from_dict(new_micro, orient='index'), worms_micro)


# Performs few operations on DF for ease of use prepare for inserting into SQLite table
def clean_df(df: DataFrame, source_sql: dict) -> DataFrame:
    df = df.filter(source_sql.keys())
    return df.rename(columns=source_sql)


# Returns comma seperated list of DataFrame columns
def csl(df: DataFrame) -> str:
    return ', '.join(df.columns.values.tolist())


con = sqlite3.connect("species_test.db")
cur = con.cursor()

write_lter()
write_phybase()
# read phybase csv
# write_phybase
# commit changes

con.close()  # closes connection
