import pandas
import sqlite3
from collections import OrderedDict
from pandas import DataFrame


def load_phybase(cursor) -> DataFrame:
    phybase_sql = OrderedDict([("decimalLatitude", "latitude"), ("decimalLongitude", "longitude"),
                               ("depth", "depth"), ("scientificName", "scientific_name"), ()])

    data: DataFrame = pandas.read_csv('datasets/phytobase.csv.csv', encoding='unicode_escape')
    df = clean_df(data, phybase_sql)
    return df


# Cleans/formats DF to match sqlite table schema
def clean_df(df: DataFrame, source_sql: OrderedDict) -> DataFrame:
    df = df.filter(source_sql.keys())  # keep only needed cols
    df.rename(columns=source_sql, inplace=True)  # rename cols using dict to match our format
    df = df[source_sql.values()]  # reorders cols to match our format
    return df


con = sqlite3.connect("species_test.db")
cur = con.cursor()
phybase_df = load_phybase(cur)
phybase_df.to_sql('temp_phybase', con=con, index=False)
phybase_cols_str = ', '.join(phybase_df.columns.values.tolist())
# Prone to SQL injection, but does not use any user input as injected values
# Inserts all values from phytobase temp table into main sample table
cur.execute(f"insert into sample ({phybase_cols_str}) select {phybase_cols_str} from temp_phybase;")
cur.execute("drop table temp_phybase")
con.commit()
con.close()
print("done")