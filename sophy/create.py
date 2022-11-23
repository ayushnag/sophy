"""Instructions to create the database from scratch. New functions are used to update the database"""
__author__ = 'Ayush Nag'

import sqlite3
import pandas as pd
import numpy as np
import geolabel
import sophysql
import sophytaxa
from pandas import DataFrame

con = sqlite3.connect("sophy.db")
cur = con.cursor()
sophysql.create_tables()

sample_worms_file: str = '../data/datasets/sample_worms.csv'
lter_file: str = '../data/datasets/modified/lter.csv'
phybase_file: str = '../data/datasets/modified/phytobase.csv'
joywarren_file: str = '../data/datasets/modified/joy_warren.csv'
joywarren_chemtax_file: str = '../data/datasets/modified/joy_warren_chemtax.csv'
joywarren_microscopy_file: str = '../data/datasets/modified/joy_warren_microscopy.csv'
alderkamp_file: str = '../data/datasets/modified/alderkamp.csv'

sample_cols: tuple = sophysql.get_table_cols("sample")
occurrence_cols: tuple = sophysql.get_table_cols("occurrence")
taxa_cols: tuple = sophysql.get_table_cols("taxonomy")


def sophy_transform(data: DataFrame) -> DataFrame:
    """Standard set of transformations specific to the SOPHY database"""
    # TODO: add drop nulls, geolabelling, etc.


def write_lter() -> None:
    """Writes LTER dataset to database"""
    sample_df: DataFrame = pd.read_csv(lter_file, encoding='unicode_escape')
    sample_df['source_name'] = 'lter'
    # drop rows with null time, lat, or long
    sample_df = sample_df.dropna(subset=['timestamp', 'longitude', 'latitude'])

    sample_df = geolabel.label_zones(sample_df, 'longitude', 'latitude').drop('index_right', axis=1)
    sample_df = geolabel.label_sectors(sample_df, 'longitude')

    sophysql.write_dataset(data=sample_df, table_name="sample")


def write_phybase() -> None:
    """Writes Phytobase dataset to database"""
    occ_df: DataFrame = pd.read_csv(phybase_file, encoding='unicode_escape')
    occ_df['source_name'] = 'phytobase'

    sci_names_data = set(occ_df['scientific_name'].unique())
    sci_names_micro = set(cur.execute("select scientific_name from taxonomy").fetchall())
    missing: set = sci_names_data - sci_names_micro  # sci_names that are missing from our database taxa records
    # get full taxonomy of microscopy data as dataframe
    taxa_df: DataFrame = pd.read_csv(sample_worms_file)  # Testing only
    taxa_df = taxa_df.rename(columns=sophytaxa.worms_sql)
    # not filtered earlier to get maximum taxa data possible for microscopy table
    occ_df = basic_filter(occ_df)
    # merge three columns into one with proper datetime format (no NaT)
    occ_df['timestamp'] = pd.to_datetime(occ_df[['year', 'month', 'day']], format='%m-%d-%Y',
                                         errors='coerce').dropna()
    occ_df = occ_df.drop(columns=['year', 'month', 'day'])
    # join on sample and taxonomy (by aphia_id), only keep cols in the occurrence table (filter out order, genus, etc)
    occ_df: DataFrame = pd.merge(occ_df, taxa_df).filter(occurrence_cols)

    occ_df = geolabel.label_zones(occ_df, 'longitude', 'latitude').drop('index_right', axis=1)
    occ_df = geolabel.label_sectors(occ_df, 'longitude')

    # write taxonomy dataframe to sql database
    sophysql.write_dataset(data=taxa_df, table_name="taxonomy")
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
    taxa_list = list(microscopy[are_taxa]['taxa'])
    taxa = sophytaxa.query_worms(taxa_list)
    # ----------------------------------
    category_conditions: list = [
        (taxa['class'] == 'Bacillariophyceae'),  # diatom
        (taxa['genus'] == 'Phaeocystis'),  # phaeo
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
    joy_warren = joy_warren.groupby([joy_warren["depth"].pct_change().abs().gt(0.15).cumsum(), "station"]).mean()
    joy_warren = joy_warren.reset_index(level=0, drop=True).reset_index(level=0).sort_values(by='depth')
    joy_warren.sort_values(by=['station', 'depth'])
    # --------------------------------------------------
    jwchemtax = pd.read_csv(joywarren_chemtax_file)
    jwchemtax['chemtax_haptophytes'] = jwchemtax['Haptophytes1_frac_chla'] + jwchemtax['Haptophytes2_frac_chla']
    jwchemtax = jwchemtax.dropna().sort_values(by='depth')
    sample: DataFrame = pd.merge_asof(jwchemtax, joy_warren, by='station', on='depth', direction='nearest',
                                      tolerance=1).sort_values(by='station')

    sample['timestamp'] = pd.to_datetime(sample['date'], format='%Y%m%d', errors='coerce').dropna().drop(
        columns=['date', 'time'])
    sample['source_name'] = 'joyw'
    extra = sample.columns.difference(sophysql.get_table_cols("sample")).drop(['station'])
    sample["extra"] = sample[extra].agg(lambda r: r[r.notna()].to_json(), axis=1)
    sample = sample.drop(columns=list(extra))
    # ----------------------------------------------------
    sample = sample.reset_index(drop=True)
    max_id = sophysql.query("select max(id) from sample")[0][0] + 1
    sample['id'] = np.arange(max_id, max_id + len(sample))

    jwmkey = pd.concat([sample['id'], sample['station'], sample['depth']], axis=1).sort_values(by='depth')

    microscopy = microscopy.sort_values(by='depth')
    microscopy = pd.merge_asof(microscopy, jwmkey, by='station', on='depth', direction='nearest', tolerance=1)
    microscopy = microscopy.rename({'id': 'sample_id', 'AphiaID': 'aphia_id', 'taxa': 'name', 'group': 'groups'},
                                   axis="columns")

    ratios = microscopy.groupby(['station', 'category', 'depth'])['biovolume'].sum() / \
             microscopy.groupby(['station']).sum()['biovolume']
    ratios = ratios.to_frame().unstack(level=1, fill_value=0).droplevel(level=0, axis=1).reset_index()
    sample = pd.merge(sample, ratios, on=['station', 'depth'], how='outer')
    sample = sample.rename(columns={"diatom": "category_diatom", "phaeocystis": "category_phaeocystis",
                                    "dinoflagellate": "category_dinoflagellate",
                                    "mixed_flagellate": "category_mixed_flagellate",
                                    "silicoflagellate": "category_silicoflagellate"})

    sample = geolabel.label_zones(sample, 'longitude', 'latitude').drop('index_right', axis=1)
    sample = geolabel.label_sectors(sample, 'longitude')

    sophysql.write_dataset(data=sample, table_name="sample")
    sophysql.write_dataset(data=microscopy, table_name="microscopy")


def write_alderkamp() -> None:
    """Writes Alderkamp 2019 dataset to database"""
    sample_df: DataFrame = pd.read_csv(alderkamp_file, encoding='unicode_escape')
    sample_df['source_name'] = 'alderkamp'
    sample_df = basic_filter(sample_df)
    # label zones and sectors
    sample_df = geolabel.label_zones(sample_df, 'longitude', 'latitude').drop('index_right', axis=1)
    sample_df = geolabel.label_sectors(sample_df, 'longitude')
    sophysql.write_dataset(data=sample_df, table_name="sample")


def write_source() -> None:
    """Writes source metadata to database"""


def write_taxonomy() -> None:
    """Writes stored WoRMS queries to database"""
    taxa_df: DataFrame = pd.read_csv(sample_worms_file)  # Testing only
    taxa_df = taxa_df.rename(columns=sophytaxa.worms_sql)
    sophysql.write_dataset(taxa_df, table_name='taxonomy')


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
write_taxonomy()
write_lter()
write_phybase()
write_joy_warren()
write_alderkamp()

con.close()  # closes connection
print('SOPHY build successful!')
