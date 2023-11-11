"""Manages interactions between data and SQL database"""
__author__ = 'Ayush Nag'

import sqlite3
import time
import pandas as pd
from pandas import DataFrame

con = sqlite3.connect("../../data/out/sophy.db")
con.row_factory = sqlite3.Row
cur = con.cursor()


def create_tables() -> None:
    """Creates tables based on schema and fields in lists"""
    with open('../schema.sql', 'r') as sql_file:
        con.executescript(sql_file.read())
    con.commit()


def get_table_cols(table: str) -> tuple:
    """List of columns in SQL table"""
    data = cur.execute(f"pragma table_info({table})").fetchall()
    if data:
        return list(zip(*data))[1]
    else:
        raise ValueError(f"Table {table} does not exist in the database")


def write_dataset(data: DataFrame, table_name: str) -> None:
    """Writes DataFrame to the SQLite table table_name:param"""
    # Columns present in data and in the destination SQL table
    common = set(data.columns.values.tolist()).intersection(set(get_table_cols(table_name)))
    assert len(common) != 0, "No columns in provided data match given table"
    # Create temp table, send data to table_name, and drop temp table
    data.to_sql("temp", con=con, index=False)
    cols_str: str = csl(list(common))
    cur.execute(f"insert into {table_name} ({cols_str}) select {cols_str} from temp")
    cur.execute(f"drop table temp")
    con.commit()


def query(query: str, readonly=True, internal=False) -> DataFrame:
    """Readonly is enabled by default so that assure user database will be preserved with each query"""
    # TODO: do some checks/give useful error messages for query
    # TODO: add stats, how long query took, rows returned, etc.
    # TODO: disable writes by default, but allowed with readonly=True
    start = time.time()
    result: DataFrame = pd.read_sql(query, con=con)
    if not internal:
        print(f"SOPHY SQL: {round(time.time() - start, 5)} seconds")
    return result


def full() -> DataFrame:
    """Returns the entire SOPhy database in a single DataFrame"""
    raise NotImplementedError


def clean_df(data: DataFrame, df_sql_map: dict) -> DataFrame:
    """Performs few operations on DF for ease of use and prepare for inserting into SQLite table"""
    data = data.filter(df_sql_map.keys())  # filter out columns that are not in the set
    return data.rename(columns=df_sql_map)  # rename columns using dict()


def csl(cols: list) -> str:
    """Converts list of values to comma separated string. Ex: [A, B, C] --> A, B, C"""
    return ', '.join(cols)
