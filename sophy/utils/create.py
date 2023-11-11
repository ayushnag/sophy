"""Instructions to create the database from scratch. New functions are used to update the database"""
__author__ = 'Ayush Nag'

import os
import sqlite3
import pandas as pd
import numpy as np
import geolabel
from sophy import sophytaxa, sophysql
from pandas import DataFrame
from tqdm.notebook import tqdm

con = sqlite3.connect("../../data/out/sophy.db")
cur = con.cursor()
sophysql.create_tables()

worms_folder: str = '../data/worms/'
lter_file: str = '../../data/in/datasets/modified/lter.csv'
phytobase_file: str = '../../data/in/datasets/mod/phytobase.csv'
joywarren_file: str = '../../data/in/datasets/modified/joy_warren.csv'
joywarren_chemtax_file: str = '../../data/in/datasets/modified/joy_warren_chemtax.csv'
joywarren_microscopy_file: str = '../../data/in/datasets/modified/joy_warren_microscopy.csv'
alderkamp_file: str = '../../data/in/datasets/modified/alderkamp.csv'

sample_cols: tuple = sophysql.get_table_cols("sample")
occurrence_cols: tuple = sophysql.get_table_cols("occurrence")
taxa_cols: tuple = sophysql.get_table_cols("taxonomy")


def sophy_transform(data: DataFrame) -> DataFrame:
    """Standard set of transformations specific to the SOPHY database"""
    # TODO: add drop nulls, geolabelling, etc.


def write_lter() -> None:
    """Writes LTER dataset to database"""
    sample_df: DataFrame = pd.read_csv(lter_file, encoding='unicode_escape')
    # drop rows with null time, lat, or long
    sample_df = sample_df.dropna(subset=['timestamp', 'longitude', 'latitude'])
    # columns to be excluded from the json combined column
    exclude_json = ['FilterCode']
    extra = sample_df.columns.difference(sophysql.get_table_cols("sample")).drop(exclude_json)
    sample_df["extra_json"] = sample_df[extra].agg(lambda r: r[r.notna()].to_json(), axis=1)

    sample_df = geolabel.label_zones(sample_df, 'longitude', 'latitude').drop('index_right', axis=1)
    sample_df = geolabel.label_sectors(sample_df, 'longitude')

    sophysql.write_dataset(data=sample_df, table_name="sample")


def write_phytobase() -> None:
    """Writes Phytobase dataset to database"""
    occ_df: DataFrame = pd.read_csv(phytobase_file, encoding='unicode_escape')
    occ_df['source_name'] = 'phytobase'
    # not filtered earlier to get maximum taxa data possible for microscopy table
    occ_df = basic_filter(occ_df)
    # merge three columns into one with proper datetime format (no NaT)
    occ_df['timestamp'] = pd.to_datetime(occ_df[['year', 'month', 'day']], format='%m-%d-%Y',
                                         errors='coerce').dropna()
    occ_df = occ_df.drop(columns=['year', 'month', 'day'])

    # get full taxonomy of microscopy data as dataframe
    taxa_df: DataFrame = pd.read_csv('../../data/in/worms/phytobase_worms.csv')[['original', 'AphiaID']]
    # join on sample and taxonomy (by aphia_id), only keep cols in the occurrence table (filter out order, genus, etc)
    occ_df = pd.merge(occ_df, taxa_df, left_on='scientific_name', right_on='original').filter(occurrence_cols)

    occ_df = geolabel.label_zones(occ_df, 'longitude', 'latitude').drop('index_right', axis=1)
    occ_df = geolabel.label_sectors(occ_df, 'longitude')

    # write occurrence dataframe to sql database
    sophysql.write_dataset(data=occ_df, table_name="occurrence")


def write_joy_warren() -> None:
    """Writes Joy-Warren 2019 dataset to database"""
    microscopy = pd.read_csv(joywarren_microscopy_file, encoding='utf-8').dropna()
    replace: dict = {'centric': 'diatom', 'pennate': 'diatom', 'unknown diatom': 'diatom',
                     'dinoflagellate': 'dinoflagellate', 'ciliate': 'mixed_flagellate',
                     'silicoflagellate': 'silicoflagellate'}
    microscopy['category'] = microscopy['taxa'].replace(replace)
    are_taxa = ~microscopy['taxa'].isin(replace.keys())
    taxa: DataFrame = pd.read_csv("../../data/in/worms/joy_warren_worms.csv", encoding='utf-8').rename(sophytaxa.worms_sql)
    # ----------------------------------
    category_conditions: list = [
        (taxa['class'] == 'Bacillariophyceae'),  # diatom
        (taxa['genus'] == 'Phaeocystis'),  # phaeocystis
        (taxa['class'] == 'Dinophyceae'),  # dinoflagellate
        (('superclass' in taxa.columns) and (taxa['superclass'] == 'Dinoflagelleta')),  # dinoflagellate
        (taxa['order'] == 'Dictyochales'),  # silicoflagellate
    ]

    categories = ["diatom", "phaeocystis", "dinoflagellate", "dinoflagellate", "silicoflagellate"]
    taxa['category'] = np.select(category_conditions, categories, default='other')
    taxa.index = microscopy[are_taxa].index
    microscopy.loc[taxa.index, 'category'] = taxa['category']
    microscopy['AphiaID'] = taxa['AphiaID']
    # -------------------------------------------------
    joy_warren: DataFrame = pd.read_csv(joywarren_file, encoding='utf-8')
    # group by depth and station: station1([1.7, 1.8, 2.1][9.7. 9.8, 10.2]...), station2...
    joy_warren = joy_warren.groupby([joy_warren["depth"].pct_change().abs().gt(0.15).cumsum(), "station"]).mean(numeric_only=True)
    joy_warren = joy_warren.reset_index(level=0, drop=True).reset_index(level=0).sort_values(by='depth')
    joy_warren.sort_values(by=['station', 'depth'])
    # --------------------------------------------------
    jwchemtax = pd.read_csv(joywarren_chemtax_file)
    jwchemtax['chemtax_haptophytes'] = jwchemtax['Haptophytes1_frac_chla'] + jwchemtax['Haptophytes2_frac_chla']
    jwchemtax = jwchemtax.dropna().sort_values(by='depth')
    sample: DataFrame = pd.merge_asof(jwchemtax, joy_warren, by='station', on='depth', direction='nearest',
                                      tolerance=2).sort_values(by='station')

    sample['timestamp'] = pd.to_datetime(sample['date'], format='%Y%m%d', errors='coerce').dropna().drop(
        columns=['date', 'time'])
    sample['source_name'] = 'joyw'
    extra = sample.columns.difference(sophysql.get_table_cols("sample")).drop(['station'])
    sample["extra_json"] = sample[extra].agg(lambda r: r[r.notna()].to_json(), axis=1)
    sample = sample.drop(columns=list(extra))
    # ----------------------------------------------------
    sample = sample.reset_index(drop=True)

    category_groups = microscopy.groupby(['station', 'category', 'depth'])['biovolume'].sum()
    station_sums = microscopy.groupby(['station']).sum(numeric_only=True)['biovolume']
    category_fractions = category_groups / station_sums
    category_fractions = category_fractions.to_frame().unstack(level=1, fill_value=0).droplevel(level=0, axis=1).reset_index()
    sample = pd.merge(sample, category_fractions, on=['station', 'depth'], how='outer')
    sample = sample.rename(columns={"diatom": "category_diatom", "phaeocystis": "category_phaeocystis",
                                    "dinoflagellate": "category_dinoflagellate",
                                    "mixed_flagellate": "category_mixed_flagellate",
                                    "silicoflagellate": "category_silicoflagellate"})

    max_id: int = sophysql.query("select max(id) from sample", internal=True)['max(id)'][0] + 1
    sample['id'] = np.arange(max_id, max_id + len(sample))

    jwmkey = pd.concat([sample['id'], sample['station'], sample['depth']], axis=1).sort_values(by='depth')

    microscopy = microscopy.sort_values(by='depth')
    microscopy = pd.merge_asof(microscopy, jwmkey, by='station', on='depth', direction='nearest', tolerance=1)
    microscopy = microscopy.rename({'id': 'sample_id', 'AphiaID': 'aphia_id', 'taxa': 'name', 'group': 'groups'},
                                   axis="columns")

    # TODO: drop duplicates is a temporary fix, need to fix zone overlap
    sample = geolabel.label_zones(sample, 'longitude', 'latitude').drop('index_right', axis=1).drop_duplicates(subset=['id'])
    sample = geolabel.label_sectors(sample, 'longitude')

    sophysql.write_dataset(data=sample, table_name="sample")
    sophysql.write_dataset(data=microscopy, table_name="microscopy")


def write_alderkamp() -> None:
    """Writes Alderkamp 2019 dataset to database"""
    sample_df: DataFrame = pd.read_csv('../../data/in/datasets/modified/alderkamp.csv', encoding='utf-8')
    sample_df['source_name'] = 'alderkamp'
    alderkamp_categories = ['category_phaeocystis', 'category_diatom', 'category_other']
    sample_df[alderkamp_categories] = sample_df[alderkamp_categories].div(100)
    sample_df = basic_filter(sample_df)
    # label zones and sectors
    sample_df = geolabel.label_zones(sample_df, 'longitude', 'latitude').drop('index_right', axis=1)
    sample_df = geolabel.label_sectors(sample_df, 'longitude')
    sophysql.write_dataset(data=sample_df, table_name="sample")


def write_source() -> None:
    """Writes source metadata to database"""


def write_taxonomy() -> None:
    """Writes stored WoRMS queries to database"""
    for file in os.listdir(worms_folder):
        if file.endswith(".csv"):
            m = pd.read_csv(worms_folder + file, encoding='utf-8').drop_duplicates(subset=['AphiaID']).rename(
                sophytaxa.worms_sql)
            sophysql.write_dataset(m, table_name='taxonomy')


def basic_filter(data: DataFrame) -> DataFrame:
    """Performs basic fixes on DF before inserting into SQLite table"""
    # keep only data in the Southern Ocean (latitude <= -30 degrees)
    data = data[data['latitude'] <= -30]
    data = data.dropna(subset=['longitude', 'latitude'])
    return data


def csl(cols: list) -> str:
    """Converts list of values to comma separated string. Ex: [A, B, C] --> A, B, C"""
    return ', '.join(cols)


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
write_alderkamp()
pbar.update(20)
pbar.close()
con.close()  # closes connection
print('SOPHY build successful!')
