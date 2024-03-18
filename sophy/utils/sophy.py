"""Instructions to create the database from scratch. New functions are used to update the database"""
__author__ = 'Ayush Nag'

import os
import sqlite3
import time
import pandas as pd
import pathlib
import hashlib
import numpy as np
import make_shapefiles
import sophytaxa
from pandas import DataFrame
from tqdm.notebook import tqdm

con = sqlite3.connect("../../data/out/sophy.db")
cur = con.cursor()

worms_folder: str = '../data/in/worms/'
lter_file: str = '../../data/in/datasets/mod/lter.csv'
phytobase_file: str = '../../data/in/datasets/mod/phytobase_occurrence.csv'
joywarren_file: str = '../../data/in/datasets/mod/joy_warren.csv'
joywarren_chemtax_file: str = '../../data/in/datasets/modified/joy_warren_chemtax.csv'
joywarren_microscopy_file: str = '../../data/in/datasets/mod/joy_warren_microscopy.csv'
alderkamp_file: str = '../../data/in/datasets/modified/alderkamp.csv'


def write_lter() -> None:
    """Writes LTER dataset to database"""
    sample_df: DataFrame = pd.read_csv(lter_file)
    sample_df['timestamp'] = pd.to_datetime(sample_df['timestamp'], errors='coerce')
    # drop rows with null time, lat, or long
    sample_df = sample_df.dropna(subset=['timestamp', 'longitude', 'latitude'])
    extra = sample_df.columns.difference(get_table_cols("sample"))
    sample_df["extra_json"] = sample_df[extra].agg(lambda r: r[r.notna()].to_json(), axis=1)

    sample_df = geolabel.label_zones(sample_df, 'longitude', 'latitude').drop('index_right', axis=1)
    sample_df = geolabel.label_sectors(sample_df, 'longitude')

    write_dataset(data=sample_df, table_name="sample")


def write_phytobase() -> None:
    """Writes Phytobase dataset to database"""
    occ_df: DataFrame = pd.read_csv(phytobase_file)
    occ_df['timestamp'] = pd.to_datetime(occ_df['timestamp'], errors='coerce')
    # get full taxonomy of microscopy data as dataframe
    taxa_df: DataFrame = pd.read_csv('../../data/in/worms/phytobase_worms.csv')[['original', 'AphiaID']]
    # join on sample and taxonomy (by aphia_id), only keep cols in the occurrence table (filter out order, genus, etc)
    occ_df = pd.merge(occ_df, taxa_df, left_on='scientific_name', right_on='original')
    occ_df = occ_df.rename(columns=sophytaxa.worms_sql).filter(get_table_cols("occurrence"))
    occ_df = geolabel.label_zones(occ_df, 'longitude', 'latitude').drop('index_right', axis=1)
    occ_df = geolabel.label_sectors(occ_df, 'longitude')
    # write occurrence dataframe to sql database
    write_dataset(data=occ_df, table_name="occurrence")


def write_joy_warren() -> None:
    """Writes Joy-Warren 2019 dataset to database"""
    microscopy = pd.read_csv(joywarren_microscopy_file, encoding='utf-8').dropna()
    sample: DataFrame = pd.read_csv(joywarren_file, encoding='utf-8')
    sample['timestamp'] = pd.to_datetime(sample['timestamp'], errors='coerce')

    extra = sample.columns.difference(get_table_cols("sample")).drop(['station'])
    sample["extra_json"] = sample[extra].agg(lambda r: r[r.notna()].to_json(), axis=1)
    sample = sample.drop(columns=list(extra))

    max_id: int = pd.read_sql("select max(id) from sample", con=con)['max(id)'][0] + 1
    sample['id'] = np.arange(max_id, max_id + len(sample))
    jwmkey = pd.concat([sample['id'], sample['station'], sample['depth']], axis=1).sort_values(by='depth')

    microscopy = microscopy.sort_values(by='depth')
    microscopy = pd.merge_asof(microscopy, jwmkey, by='station', on='depth', direction='nearest', tolerance=1)
    microscopy = microscopy.rename({'id': 'sample_id', 'AphiaID': 'aphia_id', 'taxa': 'name', 'group': 'groups'},
                                   axis="columns")

    # TODO: drop duplicates is a temporary fix, need to fix zone overlap
    sample = geolabel.label_zones(sample, 'longitude', 'latitude').drop('index_right', axis=1).drop_duplicates(
        subset=['id'])
    sample = geolabel.label_sectors(sample, 'longitude')

    write_dataset(data=sample, table_name="sample")
    write_dataset(data=microscopy, table_name="microscopy")


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

def query(query: str) -> DataFrame:
    """Readonly is enabled by default so that assure user database will be preserved with each query"""
    start = time.time()
    result: DataFrame = pd.read_sql(query, con=con)
    print(f"SOPHY SQL: {round(time.time() - start, 5)} seconds")
    return result


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


def write_taxonomy() -> None:
    """Writes stored WoRMS queries to database"""
    result = None
    for file in os.listdir('../../data/in/worms/'):
        if file.endswith(".csv"):
            new = pd.read_csv('../data/in/worms/' + file, encoding='utf-8').drop_duplicates(subset=['AphiaID']).rename(
                columns=sophytaxa.worms_sql)
            result = pd.concat([result, new], ignore_index=True)
    result = result.drop_duplicates(subset=['aphia_id'])
    write_dataset(result, table_name='taxonomy')

    def get_modified_files(data_files: list[pathlib.Path], sha_files: list[pathlib.Path]) -> list[pathlib.Path]:
        """Returns list of files that have been modified since last run"""
        modified = []
        for f in data_files:
            match = [sha for sha in sha_files if f.stem == sha.stem.split(".")[0]]
            if match:
                # sha256 file found; compare checksums
                with open(match[0], 'r') as sha_file:
                    old_sha = sha_file.read()
                    curr_sha = calc_checksum(f)
                if old_sha != curr_sha:
                    # checksum has changed; add to list of files to read
                    modified.append(f)
            else:
                # no sha256 file found; add to list of files to read and make checksum file
                modified.append(f)
                with open(os.path.join(sha_cache_dir, f.stem + ".sha256.txt"), 'w') as sha_file:
                    sha_file.write(calc_checksum(f))
        return modified

    def calc_checksum(filepath: pathlib.Path) -> str:
        """
        Generate checksum (SHA-256) for a file.
        """
        hasher = hashlib.sha256()
        with open(filepath, 'rb') as file:
            buffer = file.read(65536)  # Read file in chunks (64 KB) to handle large files
            while len(buffer) > 0:
                hasher.update(buffer)
                buffer = file.read(65536)
        return hasher.hexdigest()


def csl(cols: list) -> str:
    """Converts list of values to comma separated string. Ex: [A, B, C] --> A, B, C"""
    return ', '.join(cols)


create_tables()

sample_cols: tuple = get_table_cols("sample")
occurrence_cols: tuple = get_table_cols("occurrence")
taxa_cols: tuple = get_table_cols("taxonomy")

print("Building the SOPHY database")
# write_source()
pbar = tqdm(total=100)
write_taxonomy()
pbar.update(20)
write_lter()
pbar.update(20)
write_phytobase()
pbar.update(20)
write_joy_warren()
pbar.update(20)
# write_alderkamp()
pbar.update(20)
pbar.close()
con.close()  # closes connection
print('SOPHY build successful!')
