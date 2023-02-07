"""Defines static methods that deal with species data. This includes taxonomy web retrieval and custom group/category
transformations """
__author__ = 'Ayush Nag'

import numpy as np
import pyworms
import warnings
import pandas as pd
from pandas import DataFrame

# worms output -> sql col name. Also include columns from the original data that are needed but don't need renaming
# Ex: "class" -> "class" means col name is correct but class column is needed for calculations and/or used in database
worms_sql: dict = {"AphiaID": "aphia_id", "scientificname": "name", "authority": "authority",
                   "superkingdom": "superkingdom",
                   "kingdom": "kingdom", "phylum": "phylum", "subphylum": "subphylum", "superclass": "superclass",
                   "class": "class", "subclass": "subclass", "superorder": "superorder", "order": "orders",
                   "suborder": "suborder", "infraorder": "infraorder", "superfamily": "superfamily",
                   "family": "family", "genus": "genus", "species": "species", "modified": "modified"}


def query_worms(taxa: list, sqlformat=False, new_file='') -> DataFrame | None:
    """Finds full species composition of provided taxa. Uses WoRMS database to find data"""
    # full taxa records from WoRMS; worms = [[{}], [{}], [], [{}], ...]
    worms = pyworms.aphiaRecordsByMatchNames(taxa)  # Calls WoRMS API with pyworms package
    worms_df = pd.json_normalize(DataFrame(worms)[0])
    no_result = np.array(taxa)[worms_df['AphiaID'].isna()]  # values from provided list that were null in WoRMS query
    if len(no_result) != 0:  # outputs taxa (first 20) where WoRMS database found no result
        warnings.warn(f"No results found by WoRMS database: {str(no_result[:20])}...")
    if len(new_file) > 0:
        # Retrieves current records and appends rows with unique aphia_id's
        worms_df.to_csv('../data/worms/' + new_file + '.csv', encoding='utf-8', index=False)
        return None
    elif sqlformat:
        return worms_df.filter(worms_sql.keys()).rename(columns=worms_sql)
    else:
        return worms_df


def split_groups(data: DataFrame) -> DataFrame:
    """Creates three new columns (phaeocystis, diatoms, and other) based on chemtax columns"""
    assert {'chemtax_haptophytes', 'chemtax_diatoms'}.issubset(
        data.columns), 'chemtax_haptophytes and chemtax_diatoms are not present in the provided DataFrame'
    chemtax_other: set = {'chemtax_prasinophytes', 'chemtax_mixed_flagellates', 'chemtax_cryptophytes',
                          'chemtax_chlorophytes'}
    data['group_phaeocystis'] = data['chemtax_haptophytes']
    data['group_diatoms'] = data['chemtax_diatoms']
    extra: set = chemtax_other.intersection(data.columns)
    data['group_other'] = data[extra].sum(axis=1)
    return data


def taxa_categories(data: DataFrame) -> DataFrame:
    """Creates three new columns (phaeocystis, diatoms, and other) based on microscopy columns"""
