# Data transformation notebook guide
In: Raw dataset(s) in unmodified folder \
Out: Dataset(s) matching Sophy SQL table format

## 1. Load all raw datasets as dataframes
- Fix DtypeWarning by specifying dtype for columns. If not resolved, this will cause many problems down the line since there is inconsistency in the data.
- Open all the error columns, determine dtype, and pass it to the `dtype` parameter in the `pd.read_csv` function.

## 2. Sample
- Create dictionary that renames columns to match Sophy SQL table format 
- Ensure units match 
- Ensure essential columns like `latitude`, `longitude`, and `date_time` are present 
- Add `source`, `cruise`, `hplc_present`, `chemtax_present`, `microscopy_present`, `flowcam_present`, and `ifcb_present`
- If sample_amount is present have an `id` column (start with 1)
- Plot data and check it matches expected locations

## 3. Sample_Amount
- Ensure `sample_id` is present (achieved by joining with sample dataframe)
  - Join column will vary by dataset but example would be (station, depth)
- Ensure `taxa` column is present
  - Manually replace ambiguous entries. For example, "various dinoflagellates seen" should be replaced with "dinoflagellates". This is so the WoRMS API can find a taxa match and return the full taxonomy.
- Create dictionary that renames columns to match Sophy SQL table format 
- Ensure units match 
- Add `measurement_method` column (e.g. microscopy, flowcam, ifcb, etc.)
- Ensure essential columns like `sample_id`, `taxa`, and `measurement_method` are present (make sure that at least one of the measurement methods is present)
## 4. Occurrence
- Ensure units match
- Create dictionary that renames columns to match Sophy SQL table format
- Ensure essential columns like `latitude`, `longitude`, and `date_time` are present 
- Plot data and check it matches expected locations

## 5. Export all dataframes to `modified` folder

## Questions
**Where to fix column names if schema is changed?** \
Visit all notebooks in the `transformations` folder and update the dictionary that renames columns to match Sophy SQL table format. Also update the metadata.csv file in the `sophy` folder.

