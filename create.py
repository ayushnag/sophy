import pandas
import sqlite3

sample_col = {"Latitude": "latitude", "Longitude": "longitude", "Depth": "depth", "Temperature": "temperature",
              "Salinity": "salinity", "Density": "density"}
pigment_col = {"Prasinophytes": "prasinophytes",
               "Cryptophytes": "cryptophytes", "MixedFlagellates": "mixed_flagellates",
               "Diatoms": "diatoms", "Haptophytes": "haptophytes"}

data = pandas.read_csv('lter.csv', encoding='unicode_escape')
sci_name_df = data["sci_name"]
#  sci_name_df.rename("sample_col", axis=1, inplace=True)


sophy = sqlite3.connect("sophy_test.db")  # creates DB object in python
cursor = sophy.cursor()

# cursor.executescript(open("create-tables.sql").read())

#  sample.to_sql(name="sample_temp", con=sophy)  # saves sample df as table into sophy.db
#  pigment.to_sql(name="pigment_temp", con=sophy)

sophy.commit()  # save changes to .db file
sophy.close()  # closes connection

# write create tables.sql
# create sophy.db file

# import csv into dataframe
# modify all columns w /dataframe
# - maybe custom class with several data manip. methods
# write dataframe to sql table
# - do pk's work with this?
# import sophy.db file into python
# write sql table to sophy.db
