"""Instructions to create the database from the modified datasets"""
__author__ = "Ayush Nag"

import os
import json
import sqlite3
import pyworms
import argparse
import logging
import datetime
import pandas as pd
from tqdm import tqdm
import geopandas as gpd
import cartopy.crs as ccrs

LOG_FILE_DIR = "_resources/logs/"
MODIFIED_DATA_DIR = "../../data/datasets/modified/"
WORMS_CACHE_FILE = "_resources/worms.json"
METADATA_FILE = "../metadata.csv"
ZONES_SHAPEFILE = "../../data/shapefiles/zones/so_zones.shp"
SOPHY_XLSX_PATH = "../../sophy.xlsx"
SOPHY_DB_PATH = "../../sophy.db"
SOPHY_DEBUG_DB_PATH = "sophytest.db"
SOPHY_DEBUG_XLSX_PATH = "sophytest.xlsx"
SCHEMA_FILE = "../schema.sql"
WORMS_SQL = {"AphiaID": "aphia_id", "scientificname": "scientific_name", "authority": "authority",
             "superkingdom": "superkingdom", "kingdom": "kingdom", "phylum": "phylum", "subphylum": "subphylum",
             "superclass": "superclass", "class": "class", "subclass": "subclass", "superorder": "superorder",
             "order": "order_", "suborder": "suborder", "infraorder": "infraorder", "superfamily": "superfamily",
             "family": "family", "genus": "genus", "species": "species", "modified": "modified"}


def get_table_cols(table: str) -> tuple[str]:
    """List of columns in a SQL table"""
    return list(zip(*cur.execute(f"PRAGMA TABLE_INFO({table})").fetchall()))[1]


def main():
    """Main function for building the database"""
    # Find all the dataset directories (e.g. modified/lter2022/)
    data_directories = [name for name in os.listdir(MODIFIED_DATA_DIR)
                        if os.path.isdir(os.path.join(MODIFIED_DATA_DIR, name))]
    pbar = tqdm(data_directories, position=0, leave=True)
    for dataset in pbar:
        pbar.set_description(f"Processing {dataset}")
        logger.info(f"Processing {dataset}")

        sample_amount_path = os.path.join(MODIFIED_DATA_DIR, dataset, f"{dataset}_sample_amount.csv")
        sample_path = os.path.join(MODIFIED_DATA_DIR, dataset, f"{dataset}_sample.csv")
        occurrence_path = os.path.join(MODIFIED_DATA_DIR, dataset, f"{dataset}_occurrence.csv")

        # SAMPLE_AMOUNT
        if os.path.exists(sample_amount_path):
            df = pd.read_csv(sample_amount_path)
            assert os.path.exists(sample_path), f"{sample_amount_path} found, required file {sample_path} not found"
            assert "sample_id" in df.columns and not df["sample_id"].hasnans, f"{sample_amount_path}: sample_id column doesn't exist or contains NaN values"
            # convert df local sample_id to global sample_id
            # if result is empty, set max_id to 0
            max_id: int = cur.execute("SELECT MAX(id) from sample").fetchone()[0]
            if max_id is None:
                max_id = 0
            df["sample_id"] = df["sample_id"] + max_id
            worms_res = query_worms(df["taxa"].unique())
            # join the worms_res with the df
            df = df.merge(worms_res, left_on="taxa", right_on="scientific_name", how="left")
            # keep only the columns that are in the schema
            df = df.filter(get_table_cols("sample_amount"))
            affected = df.to_sql("sample_amount", con=con, index=False, if_exists="append")
            logger.info(f"Added {affected} rows to sample_amount table from {dataset}")
            con.commit()
        # SAMPLE
        if os.path.exists(sample_path):
            df = pd.read_csv(sample_path)
            df = geolabel_zones_sectors(df, "latitude", "longitude")
            df = json_compress(df, table="sample")
            affected = df.to_sql("sample", con=con, index=False, if_exists="append")
            logger.info(f"Added {affected} rows to sample table from {dataset}")
            con.commit()
        # OCCURRENCE
        if os.path.exists(occurrence_path):
            df = pd.read_csv(occurrence_path)
            worms_res = query_worms(df["taxa"].unique())
            df = df.merge(worms_res, left_on="taxa", right_on="scientific_name", how="left")
            df = geolabel_zones_sectors(df, "latitude", "longitude")
            df = json_compress(df, table="occurrence")
            affected = df.to_sql("occurrence", con=con, index=False, if_exists="append")
            logger.info(f"Added {affected} rows to occurrence table from {dataset}")
            con.commit()

    # Write stored WoRMS queries to database
    print("Writing WoRMS data to database")
    result = pd.DataFrame()
    cache = json.load(open(WORMS_CACHE_FILE, "r"))
    for taxon, data in cache.items():
        result = pd.concat([result, pd.DataFrame(data, index=range(len(data)))], ignore_index=True)
    result = result.rename(columns=WORMS_SQL)
    extra = result.columns.difference(get_table_cols("taxonomy"))
    result = result.drop(columns=list(extra))
    result = result.drop_duplicates(subset=["aphia_id"])
    affected = result.to_sql("taxonomy", con=con, index=False, if_exists="append")
    logger.info(f"Added {affected} rows to taxonomy table")
    con.commit()

    # Check for inconsistencies in schema and metadata file
    metadata = pd.read_csv(METADATA_FILE)
    tables = cur.execute("SELECT name FROM sqlite_master WHERE type='table';").fetchall()
    for table in tables:
        # Skip sqlite tables and the metadata table
        if table[0].startswith("sqlite_") or table[0] == "metadata":
            continue
        schema_cols = get_table_cols(table[0])
        metadata_cols = metadata[metadata["table_name"] == table[0]]["column_name"]
        # Get the cols that are different between the schema and metadata
        diff = set(schema_cols).difference(metadata_cols)
        if len(diff) > 0:
            logger.critical(f"{table[0]} table schema has columns {list(diff)} not found in metadata.csv")
    metadata.to_sql("metadata", con=con, index=False, if_exists="append")

    # Write the database to an Excel workbook
    writer = pd.ExcelWriter(sophy_xlsx_out, engine="xlsxwriter")
    pd.read_sql("SELECT * FROM sample", con=con).to_excel(writer, sheet_name="sample", index=False)
    pd.read_sql("SELECT * FROM sample_amount", con=con).to_excel(writer, sheet_name="sample_amount", index=False)
    pd.read_sql("SELECT * FROM occurrence", con=con).to_excel(writer, sheet_name="occurrence", index=False)
    pd.read_sql("SELECT * FROM taxonomy", con=con).to_excel(writer, sheet_name="taxonomy", index=False)
    pd.read_sql("SELECT * FROM metadata", con=con).to_excel(writer, sheet_name="metadata", index=False)
    writer.close()
    print(f"Database written to {sophy_xlsx_out}")


def json_compress(df: pd.DataFrame, table: str) -> pd.DataFrame:
    """Compresses columns not in the schema into a json column"""
    extra = df.columns.difference(get_table_cols(table))
    logger.warning(f"Compressing columns {list(extra)} into a json column")
    df["extra_json"] = df[extra].apply(lambda r: r.dropna().to_json(), axis=1)
    return df.drop(columns=list(extra))


def query_worms(taxa: list) -> pd.DataFrame:
    """Finds full species composition of provided taxa. Uses WoRMS database to find data"""
    assert len(taxa) > 0, "No taxa provided"
    # Use the cache to avoid querying the same taxa multiple times (unless user forces requery)
    if os.path.exists(WORMS_CACHE_FILE) and not args.force_worms:
        cache = json.load(open(WORMS_CACHE_FILE, "r"))
        missing = list(set(taxa) - cache.keys())
    else:
        cache = {}
        missing = taxa
    # query WoRMS for missing taxa
    if len(missing) > 0:
        logger.info(f"Querying WoRMS for {len(missing)} taxa...")
        worms: list = pyworms.aphiaRecordsByMatchNames(missing)  # Calls WoRMS API with pyworms package
        # create warnings for missing/unaccepted results. also requery worms if accepted names are found
        requeries = {}  # format: {old_index: new_worms_result}
        for i, taxon in enumerate(worms):
            # check if a record was not found
            if len(taxon) == 0:
                logger.critical(f"No record found for '{worms[i]}'")
            # check if the record is an unaccepted WoRMS name
            elif taxon[0]["status"] == "unaccepted":
                logger.warning(f"Unaccepted name '{(taxon[0])['scientificname']}' found for '{taxon}'")
                # if the status is unaccepted and there is an accepted name, requery for that taxonomy
                if "valid_AphiaID" in taxon[0]:
                    logger.warning(f"Replacing with accepted name: '{taxon[0]['valid_name']}'")
                    # we need to store the id from the original result and also the taxa name that was queried
                    requeries[i] = pyworms.aphiaRecordByAphiaID(taxon[0]["valid_AphiaID"])
        # replace values in worms with the requery results
        for i, requery_result in requeries.items():
            worms[i] = [requery_result]
        # cache json format: {"user_input": {worms_result_json}}
        for i, taxon in enumerate(missing):
            if len(worms[i]) > 0:
                cache[taxon] = worms[i][0]
            else:
                cache[taxon] = {}
        # write direct WoRMS results to cache
        json.dump(cache, open(WORMS_CACHE_FILE, "w+"))
    # return matching records from the cache
    cache = json.load(open(WORMS_CACHE_FILE, "r"))
    matches = [cache[taxon] for taxon in taxa if taxon in cache and len(cache[taxon]) > 0]
    result = pd.DataFrame(matches)
    # rename the columns to match the schema
    return result.filter(WORMS_SQL.keys()).rename(columns=WORMS_SQL)


def geolabel_zones_sectors(df: pd.DataFrame, lat_col: str, lon_col: str) -> pd.DataFrame:
    """Label the provided dataframe with Southern Ocean zones and sectors based on lon and lat columns"""
    assert {lon_col, lat_col}.issubset(
        df.columns), f'"{lon_col}" or "{lat_col}" are not present in the provided DataFrame'
    assert os.path.exists(
        ZONES_SHAPEFILE), "missing frontal zones shapefile; see make_shapefiles.py"
    data_gdf = gpd.GeoDataFrame(df, geometry=gpd.points_from_xy(df[lon_col], df[lat_col]),
                                crs="EPSG:4326").to_crs(crs=ccrs.SouthPolarStereo())
    zones_gdf = gpd.read_file(ZONES_SHAPEFILE).to_crs(ccrs.SouthPolarStereo())
    # Spatially join data points with zones (polygons) to get labelled data
    result_gdf = gpd.sjoin(data_gdf, zones_gdf, how="left")
    df = pd.DataFrame(result_gdf.drop(columns=['geometry', 'index_right']))
    # warn for data points that are not in any zone
    logger.warning(f"{df["front_zone"].isna().sum()} data points are not in any zone")
    assert df[lon_col].between(-180, 180).all(), "Data includes longitudes outside of range [-180, 180]"
    # Labels data by sectors (bins) and their latitude range
    # Ross Sea sector overlaps with the start and end of range: [-180, 180] so it is defined with two split ranges
    sectors_series: pd.Series = pd.cut(df[lon_col], bins=[-180, -130, -60, 20, 90, 160, 180],
                                       labels=['Ross', 'BA', 'Weddell', 'Indian', 'WPO', 'Ross'], ordered=False)
    return df.assign(sector=sectors_series)


def run_phytoclass(df: pd.DataFrame, hplc_columns: list[str]) -> pd.DataFrame:
    """Run phytoclass on the HPLC data and add groupings to dataframe"""
    # Probably use r2py interface to run a R script
    # Ex: labelled_df = r2py.run("phytoclass.r", df)
    raise NotImplementedError


def empty_database():
    """Deletes all tables in the database. Use with caution!"""
    tables = cur.execute("SELECT name FROM sqlite_master WHERE type='table';").fetchall()
    for table in tables:
        if not table[0].startswith("sqlite_"):
            cur.execute(f"DROP TABLE {table[0]};")
    con.commit()


def csl(cols: list) -> str:
    """Converts list of values to comma separated string. Ex: [A, B, C] --> A, B, C"""
    return ', '.join(cols)


# Set up logging
logging.basicConfig(filename=f"{LOG_FILE_DIR}build_{datetime.datetime.now().strftime("%Y%m%d_%H%M%S")}.log",
                    filemode='w', level=logging.DEBUG, format='%(asctime)s - %(levelname)s - %(funcName)s: %(message)s')
logger = logging.getLogger("sophy")
parser = argparse.ArgumentParser(description="Utility to build the sophy database")
parser.add_argument("--debug", action="store_true",
                    help=f"Enable debug mode (outputs a test database to {SOPHY_DB_PATH})")
parser.add_argument("--force_worms", action="store_true", help="Force requery of WoRMS database")
args = parser.parse_args()

sophy_xlsx_out = SOPHY_DEBUG_XLSX_PATH if args.debug else SOPHY_XLSX_PATH
sophy_db_out = SOPHY_DEBUG_DB_PATH if args.debug else SOPHY_DB_PATH

print(f"Building sophy database... \nDetailed diagnostics at _resources/logs/")
# Establish database connection
con = sqlite3.connect(sophy_db_out)
con.row_factory = sqlite3.Row
cur = con.cursor()
# Empty the database
empty_database()
# Create new tables
cur.executescript(open(SCHEMA_FILE, "r").read())
con.commit()
# Build the database
main()
con.close()
print("Build complete")
logger.info("Build complete")
