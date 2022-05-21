import pandas
import sqlite3
from math import nan
from collections import OrderedDict

# con = sqlite3.connect("species_test.db")
# cur = con.cursor()
# data = pandas.read_csv('phytobase.csv', encoding='unicode_escape')
# cols = data.columns.values.tolist()
# cur.executemany(f"insert into temp({cols}) values ('Ayush', 19)", ['name', 'age'])
# con.commit()
# con.close()

# list(micro_df_testing.itertuples(index=False, name=None))
import pandas as pd


def load_lter():
    # load data from csv into df
    # fix values
    # clean formatting
    # write to temp sql table
    # fk setup
    # drop temp
    lter_sql = OrderedDict([("Latitude", "longitude"), ("Longitude", "longitude"),
                            ("superkingdom", "timestamp"), ("kingdom", "depth"), ("phylum", "pressure"),
                            ("subphylum", "subphylum"), ("superclass", "superclass"), ("class", "class"),
                            ("subclass", "subclass"), ("superorder", "superorder"), ("order", "order"),
                            ("suborder", "suborder"), ("infraorder", "infraorder"), ("superfamily", "superfamily"),
                            ("family", "family"), ("genus", "genus"), ("species", "species"), ("citation", "citation")])
    data: pd.DataFrame = pandas.read_csv('lter.csv', encoding='unicode_escape')
    lter_df = clean_df(data, lter_sql)


# Cleans/formats DF to match sqlite table schema
def clean_df(df: pd.DataFrame, df_sql: OrderedDict) -> pd.DataFrame:
    df = df.filter(df_sql.keys())  # keep only needed cols
    # find all columns not in the df with set difference: cols.keys() / df.cols = missing
    missing: set = df_sql.keys() - set(df.columns.values.tolist())
    df[list(missing)] = nan  # add missing columns to df (does nothing if none are missing)
    df.rename(columns=df_sql, inplace=True)  # rename cols using dict to match our format
    df = df[list(df_sql.values())]  # reorders cols to match our format
    return df
