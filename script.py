import pandas
import sqlite3

con = sqlite3.connect("species_test.db")
data = pandas.read_csv('phytobase.csv', encoding='unicode_escape')
sample_df = data.filter(items=["scientificName"])
sample_df.to_sql('static', con=con)
con.commit()
con.close()
