"""Instructions to create the database from the modified datasets"""
__author__ = 'Ayush Nag'

import os
import json
import sqlite3
import pyworms
import warnings
import pandas as pd
import geopandas as gpd
import cartopy.crs as ccrs
import numpy as np
import pathlib
from tqdm import tqdm
# function to read in csv files from folder (default = "../data/datasets/modified")

# main
# - iterate over csv's in datasets/modified folder
# - for each csv, read in the data (sample, sample_amount, whatever's there)
# - separate functions for each kind of table and the logic needed (sample, sample_amount, etc)
# - flag parser in the main function for
# - ops: read all as df's, remove >= -30 latitude, 

# stats
# - output dense info about the database

data_dir = "../../data/datasets/modified/"
sha_cache_dir = "../_cache/sha256/"
worms_cache_file = "../_cache/worms.json"
zones_shapefile = "../../data/shapefiles/zones/so_zones.shp"
sophy_xlsx_output = "sophy2.xlsx"
schema_file = "../schema.sql"
worms_sql = {"AphiaID": "aphia_id", "scientificname": "scientific_name", "authority": "authority",
             "superkingdom": "superkingdom",
             "kingdom": "kingdom", "phylum": "phylum", "subphylum": "subphylum", "superclass": "superclass",
             "class": "class", "subclass": "subclass", "superorder": "superorder", "order": "order_",
             "suborder": "suborder", "infraorder": "infraorder", "superfamily": "superfamily",
             "family": "family", "genus": "genus", "species": "species", "modified": "modified"}
FORCE_QUERY_WORMS = False


def get_table_cols(table: str) -> tuple[str]:
    """List of columns in SQL table"""
    data = cur.execute(f"pragma table_info({table})").fetchall()
    if data:
        return list(zip(*data))[1]
    else:
        raise ValueError(f"Table {table} does not exist in the database")


def main():
    """Main function for building the database"""
    data_directories = [name for name in os.listdir(data_dir) if os.path.isdir(os.path.join(data_dir, name))]
    # Add each dataset to the database
    pbar = tqdm(data_directories, position=0, leave=True)
    for dataset in pbar:
        pbar.set_description(f"Processing {dataset}")
        # get the file called data_dir/lter2022/lter2022_sample_amount.csv
        if os.path.exists(os.path.join(data_dir, dataset, f"{dataset}_sample_amount.csv")):
            df = pd.read_csv(os.path.join(data_dir, dataset, f"{dataset}_sample_amount.csv"))
            assert "sample_id" in df.columns and not df["sample_id"].hasnans, "sample_id column contains NaN values"
            # TODO: update the sample_id column so it's corrected with the sample autoincrement id
            # - maybe do this by querying the database for the last sample_id and then adding 1 to it
            rows = cur.execute("SELECT COUNT(*) FROM sample").fetchall()
            last_id = rows[0][0]
            df["sample_id"] = np.arange(last_id + 1, last_id + 1 + len(df))

            # query worms, update taxa table, and update cache
            worms_res = query_worms(df["taxa"].unique()[:10], sqlformat=True)
            # join the worms_res with the df
            df = df.merge(worms_res, left_on="taxa", right_on="scientificname", how="left")
            df = json_compress(df, table="sample_amount")
            affected = df.to_sql("sample_amount", con=con, index=False, if_exists='append')
            print(f"Added {affected} rows to sample_amount table")
            con.commit()

        if os.path.exists(os.path.join(data_dir, dataset, f"{dataset}_sample.csv")):
            df = pd.read_csv(os.path.join(data_dir, dataset, f"{dataset}_sample.csv"))
            assert "source" in df.columns, "source column not found in dataframe"
            # df = gpd.sjoin(df, zones_gpd, how="left", op="intersects")
            df = geolabel_zones_sectors(df, "latitude", "longitude")
            df = json_compress(df, table="sample")
            affected = df.to_sql("sample", con=con, index=False, if_exists='append')
            print(f"Added {affected} rows to sample table")
            con.commit()

        if os.path.exists(os.path.join(data_dir, dataset, f"{dataset}_occurrence.csv")):
            raise NotImplementedError
            df = pd.read_csv(os.path.join(data_dir, dataset, f"{dataset}_occurrence.csv"))
            assert "source" in df.columns, "source column not found in dataframe"
            worms_res = query_worms(df["taxa"].unique()[:10], sqlformat=True)
            df = df.merge(worms_res, left_on="taxa", right_on="scientificname", how="left")
            df = geolabel_zones_sectors(df, "latitude", "longitude")
            df = json_compress(df, table="occurrence")
            affected = df.to_sql("occurrence", con=con, index=False, if_exists='append')
            print(f"Added {affected} rows to occurrence table")
            con.commit()

    # Write stored WoRMS queries to database
    result = pd.DataFrame()
    cache = json.load(open(worms_cache_file, "r"))
    for taxon, data in cache.items():
        result = pd.concat([result, pd.DataFrame(data, index=range(len(data)))], ignore_index=True)
    result = result.rename(columns=worms_sql)
    extra = result.columns.difference(get_table_cols("taxonomy"))
    result = result.drop(columns=list(extra))
    result = result.drop_duplicates(subset=["aphia_id"])
    affected = result.to_sql("taxonomy", con=con, index=False, if_exists='append')
    print(f"Added {affected} rows to taxonomy table")
    con.commit()

    # Write the database to an Excel workbook
    writer = pd.ExcelWriter(sophy_xlsx_output, engine='xlsxwriter')
    pd.read_sql('select * from sample', con=con).to_excel(writer, sheet_name='sample', index=False)
    pd.read_sql('select * from sample_amount', con=con).to_excel(writer, sheet_name='sample_amount', index=False)
    pd.read_sql('select * from occurrence', con=con).to_excel(writer, sheet_name='occurrence', index=False)
    pd.read_sql('select * from taxonomy', con=con).to_excel(writer, sheet_name='taxonomy', index=False)
    writer.close()
    print(f"Database written to {sophy_xlsx_output}")


def json_compress(df: pd.DataFrame, table: str) -> pd.DataFrame:
    """Compresses columns not in the schema into a json column"""
    extra = df.columns.difference(get_table_cols(table))
    df["extra_json"] = df[extra].agg(lambda r: r[r.notna()].to_json(), axis=1)
    return df.drop(columns=list(extra))


def query_worms(taxa: list, sqlformat=False) -> pd.DataFrame:
    """Finds full species composition of provided taxa. Uses WoRMS database to find data"""
    assert len(taxa) > 0, "No taxa provided"
    if os.path.exists(worms_cache_file) and not FORCE_QUERY_WORMS:
        cache = json.load(open(worms_cache_file, "r"))
        missing = set(taxa) - set(cache.keys())
    else:
        cache = {}
        missing = set(taxa)
    if len(missing) > 0:
        print(f"Querying WoRMS for {len(missing)} taxa...")
        worms = pyworms.aphiaRecordsByMatchNames(list(missing))  # Calls WoRMS API with pyworms package
        # update the cache so that keys are the input from the user (taxa) and the values are the results from worms
        for i, taxon in enumerate(missing):
            cache[taxon] = worms[i][0]
        json.dump(cache, open(worms_cache_file, "w+"))

    # return matching records from the cache
    cache = json.load(open(worms_cache_file, "r"))
    matches = [cache[taxon] for taxon in taxa]
    result = pd.DataFrame(matches)
    if sqlformat:
        return result.filter(worms_sql.keys()).rename(columns=worms_sql)
    else:
        return result


def geolabel_zones_sectors(df: pd.DataFrame, lat_col: str, lon_col: str) -> pd.DataFrame:
    """Label the dataframe with zones and sectors based on lat and lon columns"""
    assert {lon_col, lat_col}.issubset(
        df.columns), f'"{lon_col}" or "{lat_col}"are not present in the provided DataFrame'
    # assert (df[lat_col] <= -30).all(), "Provided latitude is not in the Southern Ocean (must be less than -30 degrees)"
    assert os.path.exists(
        zones_shapefile), 'missing frontal zones shapefile; try running create_fronts_zones_shapes()'

    data_gdf = gpd.GeoDataFrame(df, geometry=gpd.points_from_xy(df[lon_col], df[lat_col]), crs='EPSG:4326')
    data_gdf = data_gdf.to_crs(crs=ccrs.SouthPolarStereo())

    zones_gdf = gpd.read_file(zones_shapefile).to_crs(ccrs.SouthPolarStereo())
    # Spatially join data points with zones (polygons) to get labelled data
    result = gpd.sjoin(data_gdf, zones_gdf)
    df = pd.DataFrame(result.drop(columns='geometry'))

    assert df[lon_col].between(-180, 180).all(), f"Data includes longitudes outside of range [-180, 180]"
    # Labels data by sectors (bins) and their latitude range
    # Ross Sea sector overlaps with the start and end of range: [-180, 180] so it is defined with two split ranges
    sectors_series: pd.Series = pd.cut(df[lon_col], bins=[-180, -130, -60, 20, 90, 160, 180],
                                       labels=['Ross', 'BA', 'Weddell', 'Indian', 'WPO', 'Ross'], ordered=False)
    return df.assign(sector=sectors_series)


def run_phytoclass(df: pd.DataFrame, hplc_columns: list[str]) -> pd.DataFrame:
    """Run phytoclass on the HPLC data and add groupings to dataframe"""
    # TODO: run phytoclass using the given hplc columns
    # probably use r2py interface to run a R script
    # Idea: r2py.run("phytoclass.r", df)
    raise NotImplementedError


def clear_database():
    """Removes all tables in the database. Use with caution!"""
    tables = cur.execute("SELECT name FROM sqlite_master WHERE type='table';").fetchall()
    for table in tables:
        cur.execute(f"DELETE FROM {table[0]}")
    con.commit()


def csl(cols: list) -> str:
    """Converts list of values to comma separated string. Ex: [A, B, C] --> A, B, C"""
    return ', '.join(cols)


con = sqlite3.connect("test.db")
con.row_factory = sqlite3.Row
cur = con.cursor()

# Clear the database
clear_database()
# Create new tables
cur.executescript(open(schema_file, "r").read())
con.commit()

main()
con.close()

# write_sample_amount
# - need's sample_id column to be filled (throw error if not)
# - query worms if not in cache

# write_sample
# - compress cols not in schema.sql into a json column
# - give it an actual id column (just add current db last index)

# write_occurrence

# function for querying worms
# - should take df or array of scientific names and 
# at which stage is the caching done?
# ok for now pick the simplest solution which is to only update when there is a new dataset
# - basically if there is an entry already for that dataset, don't update it

# function for geo labelling
# - should take dataframe and column names for lat and long
# - should return dataframe with zones and sectors
# also store a cache and only run when a new dataset is added
