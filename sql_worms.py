import pandas as pd
import sqlite3
import pyworms
import time
from collections import OrderedDict
from math import nan

# Order MUST match the SQLite table exactly ("FROM", "TO")
worms_micro = OrderedDict([("AphiaID", "aphia_id"), ("scientificname", "scientific_name"),
                           ("superkingdom", "superkingdom"), ("kingdom", "kingdom"), ("phylum", "phylum"),
                           ("subphylum", "subphylum"), ("superclass", "superclass"), ("class", "class"),
                           ("subclass", "subclass"), ("superorder", "superorder"), ("order", "order"),
                           ("suborder", "suborder"), ("infraorder", "infraorder"), ("superfamily", "superfamily"),
                           ("family", "family"), ("genus", "genus"), ("species", "species"), ("citation", "citation")])

con = sqlite3.connect("species_test.db")
cur = con.cursor()

data = pd.read_csv('phytobase.csv', encoding='unicode_escape')  # full DF from dataset
sample_df = data.filter(items=["scientificName"])  # sci_name entries per row of source dataset


# Gets the full WoRMS taxonomy of every unique sci_name in sample_df, returns DF
def get_microscopy_df() -> pd.DataFrame:
    micro = pd.DataFrame()
    taxa = set()  # should get current sci_names from the DB first
    for row in range(1000):  # iterate through DF for real version
        name: str = sample_df.at[row, "scientificName"]
        # assert @check, "invalid name at ___"
        if name not in taxa:
            result: list = pyworms.aphiaRecordsByMatchNames(name)[0]  # full taxa records from WoRMS
            if len(result) > 0:  # when WoRMS doesn't find a matching record, len(result) = 0
                taxa.add(name)
                micro = pd.concat([micro, pd.DataFrame([result[0]])])
            else:
                raise ValueError(f'Invalid scientific name (row {row}): {name}')
    return micro


# Cleans/formats microscopy DF to match sqlite table schema
def clean_microscopy_df(df: pd.DataFrame) -> pd.DataFrame:
    df = df.filter(worms_micro.keys())  # keep only needed cols
    # find all columns not in the df with set difference: cols.keys() / df.cols = missing
    missing: set = worms_micro.keys() - set(df.columns.values.tolist())
    df[list(missing)] = nan  # add missing columns to df (does nothing if none are missing)
    df.rename(columns=worms_micro, inplace=True)  # rename cols using dict to match our format
    df = df[list(worms_micro.values())]  # reorders cols to match our format
    return df


# calculate and clean taxonomy DF using original dataset DF (sample_df)
# micro_df = get_microscopy_df()
micro_df: pd.DataFrame = clean_microscopy_df(pd.read_csv('micro.csv'))  # for testing use only

start: float = time.time()
micro_df.to_sql('temp_micro', con=con, index=False)
# copy into table w/ correct schema
cur.execute("insert into microscopy select * from temp_micro")
cur.execute("drop table temp_micro")

sample_df.to_sql('temp_sample', con=con)
# inserts sci_name's and matching aphia_id's into sample
# inner join on sample and microscopy to get matching aphia_id for each sci_name in sample
cur.execute("insert into sample(scientificName, aphia_id) select t.scientificName, "
            "(select m.aphia_id from microscopy m where t.scientificName = m.scientific_name) from temp_sample t;")
cur.execute("drop table temp_sample")

print(f"SQLite operations took {time.time() - start} seconds")
con.commit()
con.close()
print("done")
