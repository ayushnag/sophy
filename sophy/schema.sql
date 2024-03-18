CREATE TABLE IF NOT EXISTS sample (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    source TEXT,
    cruise TEXT,

    -- location(s) and time
    latitude REAL,
    longitude REAL,
    timestamp TEXT,
    front_zone TEXT,
    sector TEXT,

    -- chem/phys variables
    depth REAL,
    chl_a_fluor REAL,
    salinity REAL,
    temperature REAL,
    dic REAL,
    tot_alkalinity REAL,
    poc REAL,
    oxygen REAL,
    mld REAL,
    euphotic_depth REAL,
    par REAL,

    -- nutrients
    dfe REAL,
    nitrate REAL,
    nitrite REAL,
    nitrate_nitrite REAL,
    phosphate REAL,
    silicate REAL,

    -- species composition
    chemtax_prasinophytes REAL,
    chemtax_cryptophytes REAL,
    chemtax_chlorophytes REAL,
    chemtax_dinoflagellates REAL,
    chemtax_mixed_flagellates REAL,
    chemtax_diatoms REAL,
    chemtax_haptophytes REAL,

    -- primary pigments
    hplc_allo REAL,
    hplc_alpha_car REAL,
    hplc_beta_car REAL,
    hplc_alpha_beta_car REAL,
    hplc_but_fuco REAL,
    hplc_diadino REAL,
    hplc_diato REAL,
    hplc_fuco REAL,
    hplc_hex_fuco REAL,
    hplc_perid REAL,
    hplc_tot_chl_a REAL,
    hplc_tot_chl_b REAL,
    hplc_tot_chl_c REAL,
    hplc_zea REAL,

    -- secondary pigments
    hplc_chl_c3 REAL,
    hplc_chlide_a REAL,
    hplc_dv_chl_a REAL,
    hplc_dv_chl_b REAL,
    hplc_mv_chl_a REAL,
    hplc_mv_chl_b REAL,
    hplc_chl_c2 REAL,
    hplc_mv_chl_c3 REAL,
    hplc_chl_c12 REAL,
    hplc_chl_c2_mgdg REAL,
    hplc_chl_c2_mgdg_14 REAL,
    hplc_chl_c2_mgdg_18 REAL,
    hplc_mgdvp REAL,

    -- tertiary pigments
    hplc_lut REAL,
    hplc_neo REAL,
    hplc_phide_a REAL,
    hplc_phide_b REAL,
    hplc_phytin_a REAL,
    hplc_phytin_b REAL,
    hplc_pyrophaeo_a REAL,
    hplc_pras REAL,
    hplc_viola REAL,

    -- ancillary pigment
    hplc_gyro REAL,

    -- measurement methods
    hplc_present INTEGER,
    chemtax_present INTEGER,
    microscopy_present INTEGER,
    flowcam_present INTEGER,
    ifcb_present INTEGER,

    -- JSON extra column
    extra_json TEXT
) STRICT;

-- occurrence only data
CREATE TABLE IF NOT EXISTS occurrence (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    source TEXT,
    aphia_id INTEGER REFERENCES taxonomy(aphia_id),
    taxa TEXT,
    latitude REAL,
    longitude REAL,
    depth REAL,
    timestamp TEXT,
    front_zone TEXT,
    sector TEXT,
    extra_json TEXT
) STRICT;

-- additional observational data along with sample
CREATE TABLE IF NOT EXISTS sample_amount (
    sample_id INTEGER REFERENCES sample(id),
    aphia_id INTEGER REFERENCES taxonomy(aphia_id),
    taxa TEXT,
    biomass_per_L REAL,
    biovolume_per_L REAL,
    cells_per_L REAL,
    count_per_L REAL,
    measurement_method TEXT
) STRICT;

-- full taxonomy of species
CREATE TABLE IF NOT EXISTS taxonomy (
    aphia_id INTEGER PRIMARY KEY,
    scientific_name TEXT,
    authority TEXT,
    superkingdom TEXT,
    kingdom TEXT,
    phylum TEXT,
    subphylum TEXT,
    superclass TEXT,
    class TEXT,
    subclass TEXT,
    superorder TEXT,
    order_ TEXT,
    suborder TEXT,
    infraorder TEXT,
    superfamily TEXT,
    family TEXT,
    genus TEXT,
    species TEXT,
    modified TEXT
) STRICT;