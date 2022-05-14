import pandas as pd
import sqlite3
import pyworms
import time

microscopy_cols = ["aphia_id", "scientific_name", "superkingdom", "kingdom", "phylum", "subphylum",
                   "superclass", "class", "subclass", "superorder", "order", "suborder", "infraorder",
                   "superfamily", "family", "genus", "species", "citation"]

worms_micro = {"AphiaID": "aphia_id", "scientificname": "scientific_name", "superkingdom": "superkingdom",
               "kingdom": "kingdom", "phylum": "phylum", "subphylum": "subphylum", "superclass": "superclass",
               "class": "class", "subclass": "subclass", "superorder": "superorder", "order": "order",
               "suborder": "suborder", "infraorder": "infraorder", "superfamily": "superfamily",
               "family": "family", "genus": "genus", "species": "species", "citation": "citation"}

con = sqlite3.connect("species_test.db")
cur = con.cursor()

data = pd.read_csv('phytobase.csv', encoding='unicode_escape')  # full DF from dataset
sample_df = data.filter(items=["scientificName"])  # sci_name entries per row of source dataset

micro_df_testing = pd.DataFrame({"aphia_id": [248106, 620590, 178590, 376694, 134546],
                                 "sci_name": ["Carteria marina", "Coccopterum labyrinthus",
                                              "Dunaliella tertiolecta", "Halosphaera minor",
                                              "Halosphaera viridis"]})  # for testing use only


# Gets the full WoRMS taxonomy of every unique sci_name in sample_df, returns DF
def get_microscopy_df():
    micro = pd.DataFrame()
    taxa = set()  # uses set() rather than repeatedly searching through DF for efficiency
    for row in range(500):  # iterate through DF for real version
        name = sample_df.at[row, "scientificName"]
        if name not in taxa:
            result = pyworms.aphiaRecordsByMatchNames(name)[0]
            if len(result) > 0:  # when WoRMS doesn't find a matching record, len(result) = 0
                taxa.add(name)
                micro = pd.concat([micro, pd.DataFrame([result[0]])])
    return micro


# Cleans/formats microscopy DF to match sqlite table schema
def clean_microscopy_df(df):
    df = df.filter(worms_micro.keys())  # keep only needed cols
    # find all columns not in the df with set difference: cols.keys() / df.cols = missing
    missing = worms_micro.keys() - set(df.columns.values.tolist())
    df[list(missing)] = None  # add missing columns to df
    df.rename(columns=worms_micro, inplace=True)  # rename cols to match our format
    df = df[microscopy_cols]  # reorders cols to match our format
    return df


# calculate and clean taxonomy DF using original dataset DF (sample_df)
micro_df = get_microscopy_df()
micro_df = clean_microscopy_df(micro_df)

start = time.time()
# temp table w/ taxonomies
micro_df.to_sql('temp_micro', con=con, index=False)
# copy into table w/ correct schema
cur.execute("insert into microscopy select * from temp_micro")
# delete temporary table
cur.execute("drop table temp_micro")

# temp table w/ scientificNames
sample_df.to_sql('temp_sample', con=con)
# inserts sci_name's and matching aphia_id's into sample
# inner join on sample and microscopy to get matching aphia_id for each sci_name in sample
cur.execute("insert into sample(scientificName, aphia_id) select t.scientificName, "
            "(select m.aphia_id from microscopy m where t.scientificName = m.scientific_name) from temp_sample t;")
# delete temporary table
cur.execute("drop table temp_sample")

print(f"SQLite operations took {time.time() - start} seconds")
con.commit()
con.close()
print("done")
