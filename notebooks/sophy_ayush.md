# SOPHY Notes

### Feature Ideas
- Think about how this could be adapted to the future of phytoplankton data
  - For example if Argo floats may start having taxa data
  - Or just any sensor based data that includes taxa because our current model is just for _in situ_ observations
- What are side 'features/products' that I can make for SOPHY and general use
  - Adapter class that provides starter code for converting dataset into SQLite

### Spring Quarter 2022 Wrap-Up
- Feature List:
  - Main script can add two full datasets to database (~1.3 mil rows)
    - _LTER_ and _Phytobase_ were chosen since they cover the two different formats of taxonomy data (microscopy and CHEMTAX)
    - Also adds foreign keys from microscopy table (Phytobase)
  - Query WoRMS database for taxa records
    - Converts result from pyworms package into formatted dataframe
  - **Modular code** that easily translates to other datasets
    - Code from this quarter is quite short since I have reviewed each operation several times to prioritize simplicity and performance as a setup for the summer
    - The formula is made for how to add new datasets; data read, modify, write, and fk setup
- Next steps:
  - Support for location, source, and tag tables as part of data insert
  - Work on test suite even though code format may change (new classes/functions)
  - Build collection of datasets we want to add to SOPHY
    - Can be done concurrently with writing new code
    - The schema and code will adapt to deal with new challenges or design changes
  - How to interact with the database?
    - Research how scientific databases are usually presented (GUI, Jupyter, etc.)
    - We can make pre-built use cases for common operations

### Iterating over a Dataframe
- I was finding methods to iterate over a dataframe such as itterows(), but operations seemed to be taking longer than expected (~2s)
- Across several functions, I was incorrectly iterating over a dataframe rather than **vectorization** and using pandas built in indexing
- **Vectorization** means using pre-defined, highly optimized methods to process data
- The time complexity and runtime is orders of magnitude lower when using vectorization since DataFrame's are meant to use it

### Natural Key vs AphiaID
- Datasets that contain microscopy data will most likely contain a 'scientific_name' field that we will also have a corresponding AphiaID we will get from the WoRMS database
- sci_name is a key for aphia_id and vice versa so we should only store one of them in the main table
- However not all microscopy data goes to the level of sci_name and may only go down to genus
- In that case the aphia_id approach is correct since we can keep the aphia_id for the genus and then have access to it's full taxa through the microscopy table whereas that would not be possible with only a sci_name col in the main table
- This approach also correctly handles the issue of when two names are different in Python or just visually, but actually represent the same species (WoRMS flags species name as unaccepted)
```python
pyworms.aphiaRecordsByMatchNames('Coccopterum labyrinthus')  # accepted name
pyworms.aphiaRecordsByMatchNames('Coccopterum_labyrinthus')  # slightly different formatting
pyworms.aphiaRecordsByMatchNames('Pterosperma labyrinthus')  # unaccepted name, but same species
```
- A rank column may also be useful however it seems like data that can be inferred from what data is present and not present, so TBD

### Defining geospatial regions in the Southern Ocean
- We want to be able to label rows with a certain regions like the one seen in the map:
  <img alt="Southern Ocean Map" src="southern_ocean.jpg" title="Southern Ocean Map" width="300"/>
- Cannot use simple lat long filters since they are rectangular unlike our regions
- Solutions inlcude ArcGIS filter/map or polygons that have predefined these regions
- Main point is that there must be a mapping from latitude to region
- If one is not available, we can explore how to create that mapping
- Mapping can and should be done at insert time, not runtime to speed up queries that use this data
- Some options are GeoPandas, [GeoJSON](https://handsondataviz.org/geojsonio.html), ArcGIS, PostGIS, pyshp, PyGIS, and arcpy
- An issue with the Arc family is that they are not open-source unlike GeoJSON and others

### Workflow of Python and SQLite
- Both have a way of storing large amounts of 2D data(dataframes vs. tables) so it can be confusing when to use which
- Dataframes are much easier to modify, can be used alongside python code, and keeps history of operation
- SQLite is [much faster](https://www.thedataincubator.com/blog/2018/05/23/sqlite-vs-pandas-performance-benchmarks/) at select style operations
- Data loading, cleanup, and write to database will be done in Python with dataframes 
- Then queries only with SQLite

### Re-normalization of columns: major fix
- Updated schema to avoid normalizing much more than needed (3 FK's in schema)
- I used to create a whole new cruise table since I thought repeating a string in the same column was repeated data that needed to be fixed
- **Normalization means when one column can allow you to infer other columns**
  - For example when knowing the source name (LTER) can tell you author, doi, url, etc. and that data doesn't need to be repeated across many columns
  - One **key** gives you access to the other columns
  - Then that data goes in a new table and the main table simply references that one key to have access to the rest of the data
  - It's ok to repeat values within a column, but there shouldn’t be columns that infer other columns within a table
- This change has drastically reduced the number of tables in the DB (see schema v5 &rarr; v6)

### Primary Key Setup
- They can be auto-generated in SQLite, but is that the best way?
```sql
id int primary key autoincrement
```
- Some alternatives are GUID, UUID, and natural keys
- The key does not need to be unique across the database so GUID is probably overkill
- Autoincrement is the best option for now since it also the default option in SQLite

### Tech Stack
- Dataset(CSV) &rarr; DataFrame(Python) &rarr; sophy(SQLite)
- Sophy can be created in sqlite (createTables.sql) then saved as an .db file to insert data with Python
- First test is to load the LTER dataset through the tech stack

### Column that can hold id of two possible tables
- The problem is called Polymorphic Associations
- I would like to reference two tables to the same column with an FK
  - For example microscopy id OR taxa id
- One fix is to make a supertable that generates a primary key, then the two 'sub' tables reference their id from the super table
- This is essentially a PFK (primary foreign key) since each row in the sub tables is unique but technically still a foreign key
- The only issue is that it complicates the schema and doing queries since there is an extra table needed to do inserts

### Phytoplankton microscopy vs. pigment based taxa classification
- I originally thought  each (in situ) dataset would provide a species name that could be converted into a taxonomy tree (using microscopy)
- In reality they provide either microscopy OR pigment data. Both provide a classification of the taxonomy of each sample
- Pigments are the chemical method by using pigment markers and the CHEMTAX software to determine the species composition of a water sample. CHEMTAX gives the percentage of ~5 groups to determine species comp.
- The schema needs to be restructured to reflect this change. One row in one dataset represents a full water sample(pigments) but one row in another dataset represents the amount of each species found (microscopy). Since they are inherently different row structures, a new table may be needed.

### Tags
- We need to be able to classify rows with certain data like the method of sampling, quality of data, etc
- Tags are a great way to do this since we can create a tag, then reuse that same tag for several rows
- Represented by a many &rarr; many relationship in SQL.

### WoRMS Database
- We will be using [WoRMS](https://www.marinespecies.org/) since it is the most relevant and established database for our research
- All taxonomy data will be sourced from there
- There is Python package that allows us to query the DB and get the full taxa of a species
```python
import pyworms
pyworms.aphiaRecordsByMatchNames('Carteria marina')
```

### Database Planning ###
- Who are the users?
  - Researchers (oceanography most likely)
  - They have experience with Python and Jupyter notebooks
  - Should make a document on how to use the program
- RDMS vs. Excel/CSV
  - CSV will get slow in the range of millions of columns to even just search
  - Major benefits will be seen when making the niche model
    - Researchers may not have super complex queries but the niche model will
    - The model will be **significantly** faster at runtime (visualization)
  - Data is also much easier to add since structure is clearly defined







