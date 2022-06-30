import pandas
import sqlite3
from collections import OrderedDict
from pandas import DataFrame


def load_lter(cursor) -> DataFrame:
    # load data from csv into df
    # fix values
    # clean formatting
    # write to temp sql table
    # fk setup
    # drop temp
    lter_sql = OrderedDict([("Latitude", "latitude"), ("Longitude", "longitude"), ("DatetimeGMT", "timestamp"),
                           ("Depth", "depth"), ("Salinity", "salinity"), ("Temperature", "temperature"),
                           ("Density", "density"), ("Chlorophyll", "chlorophyll"), ("Phaeopigment", "phaeopigments"),
                           ("Fluorescence", "fluorescence"), ("PrimaryProduction", "primary_prod"),
                           ("studyName", "cruise"), ("PAR", "down_par"), ("Prasinophytes", "prasinophytes"),
                           ("Cryptophytes", "cryptophytes"), ("MixedFlagellates", "mixed_flagellates"),
                           ("Diatoms", "diatoms"), ("Haptophytes", "haptophytes"), ("NO3", "nitrate"),
                           ("NO2", "nitrite"), ("DIC1", "diss_inorg_carbon"), ("DOC", "diss_org_carbon"),
                           ("POC", "part_org_carbon"), ("SiO4", "silicate"), ("N", "tot_nitrogen"),
                           ("PO4", "phosphate"), ("Notes1", "notes")])

    data: DataFrame = pandas.read_csv('../datasets/lter.csv', encoding='unicode_escape')
    df = clean_df(data, lter_sql)
    return df


# Cleans/formats DF to match sqlite table schema
def clean_df(df: DataFrame, source_sql: OrderedDict) -> DataFrame:
    df = df.filter(source_sql.keys())  # keep only needed cols
    df.rename(columns=source_sql, inplace=True)  # rename cols using dict to match our format
    df = df[source_sql.values()]  # reorders cols to match our format
    return df


con = sqlite3.connect("sophy.db")
cur = con.cursor()
lter_df = load_lter(cur)
lter_df.to_sql('temp_lter', con=con, index=False)
lter_cols_str = ', '.join(lter_df.columns.values.tolist())
# Prone to SQL injection, but does not use any user input as injected values
# Inserts all values from lter temp table into main sample table
cur.execute(f"insert into sample ({lter_cols_str}) select {lter_cols_str} from temp_lter")
cur.execute("drop table temp_lter")
con.commit()
con.close()
print("done")
