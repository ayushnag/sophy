"""Defines static methods that deal with species data. This includes taxonomy web retrieval and custom group/category
transformations """
__author__ = 'Ayush Nag'

import pyworms
import warnings
import pandas as pd
from pandas import DataFrame

# worms output -> sql col name. Also include columns from the original data that are needed but don't need renaming
# Ex: "class" -> "class" means col name is correct but class column is needed for calculations and/or used in database
worms_sql: dict = {"AphiaID": "aphia_id", "scientificname": "scientific_name", "authority": "authority",
                   "superkingdom": "superkingdom",
                   "kingdom": "kingdom", "phylum": "phylum", "subphylum": "subphylum", "superclass": "superclass",
                   "class": "class", "subclass": "subclass", "superorder": "superorder", "order": "t_order",
                   "suborder": "suborder", "infraorder": "infraorder", "superfamily": "superfamily",
                   "family": "family", "genus": "genus", "species": "species", "modified": "modified"}


def update_sample_worms(taxa: list) -> None:
    """Finds full species composition of provided taxa. Uses WoRMS database to find data"""
    microscopy, no_result = [], []
    # full taxa records from WoRMS; worms = [[{}], [{}], [], [{}], ...]
    worms: list = pyworms.aphiaRecordsByMatchNames(taxa)
    for i, taxonomy in enumerate(worms):
        if len(taxonomy) > 0:
            microscopy.append(taxonomy)
        else:  # no WoRMS record was found since len(result) = 0
            no_result.append(taxa[i])
    if len(no_result) != 0:  # outputs taxa (first 20) where WoRMS database found no result
        warnings.warn(f"No results found by WoRMS database: {str(no_result[:20])}...")
    # convert list of dict() -> dataframe and clean it
    new = DataFrame(microscopy).rename(worms_sql)
    curr = pd.read_csv("../data/datasets/sample_worms.csv")
    full: DataFrame = new.append(curr)
    full = full.drop_duplicates(subset=['aphia_id'])
    full.to_csv("../data/datasets/sample_worms.csv", encoding='utf-8', index=False)


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
