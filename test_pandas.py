import pandas
import sqlite3
import pyworms
import time

data = pandas.read_csv('phytobase.csv', encoding='unicode_escape')  # full DF from dataset
sample_df = data.filter(items=["scientificName"])  # sci_name entries per row of source dataset
micro_df = pandas.DataFrame(columns=["aphia_id", "sci_name"])  # microscopy table

micro_df_testing = pandas.DataFrame({"aphia_id": [248106, 620590, 178590, 376694, 134546],
                                     "sci_name": ["Carteria marina", "Coccopterum labyrinthus",
                                                  "Dunaliella tertiolecta", "Halosphaera minor",
                                                  "Halosphaera viridis"]})  # for testing use only

con = sqlite3.connect("species_test.db")
cur = con.cursor()


# cur.executemany("insert into sample(sci_name) values (?)", tuple(sci_name_df))
def calc_micro_df():
    taxa = set()  # uses set() rather than repeatedly searching through DF for efficiency
    for row in range(500):  # iterate through DF for real version
        name = sample_df.at[row, "scientificName"]
        if name not in taxa:
            result = pyworms.aphiaRecordsByMatchNames(name)[0]
            if len(result) > 0:  # when WoRMS doesn't find a matching record, len(result) = 0
                taxa.add(name)
                micro_df.loc[row, ['aphia_id', 'sci_name']] = [result[0].get('AphiaID'), name]


start = time.time()

# temp table w/ calculated microscopy data
# micro_df.to_sql('temp', con=con)
# insert into microscopy table w/ proper schema
# cur.execute("insert into microscopy(aphia_id, sci_name) select aphia_id, sci_name from temp")
# delete temporary table
# cur.execute("drop table temp")
cur.executemany("insert into microscopy(aphia_id, sci_name) values(?, ?)",
                list(micro_df_testing.itertuples(index=False, name=None)))

# OPTIMIZE USING ABOVE METHOD*****
# temp table w/ scientificNames
sample_df.to_sql('temp_sample', con=con)
# insert scientificNames into sample table

# inserts sci_name's and matching aphia_id's into sample
cur.execute("insert into sample(scientificName, aphia_id) select t.scientificName, "
            #  inner join on sample and microscopy to get matching aphia_id for each sci_name in sample
            "(select m.aphia_id from microscopy m where t.scientificName = m.sci_name) from temp_sample t")
# delete temporary table
cur.execute("drop table temp_sample")

print(f"SQLite operations took {time.time() - start} seconds")
con.commit()
con.close()
print("done")

# taxa = dict()
# fk = list()
# for row in range(1000):
#     name = sci_name_df[row]
#     if name not in taxa.keys():
#         result = pyworms.aphiaRecordsByMatchNames(name)[0]
#         if len(result) > 0:
#             taxa[name] = result[0].get('AphiaID')
#         else:
#             taxa[name] = -1
#     fk.append(taxa.get(name))
# print("done")
