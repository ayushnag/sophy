create table if not exists sample (
    id integer primary key autoincrement,
    source_name text references source(name),

    latitude real,
    longitude real,
    timestamp text,
    front_zone text,
    sector text,

    depth real,
    pressure real,
    salinity real,
    temperature real,
    density real,
    mld real,
    chlorophyll_a_fluor real,
    nitrate real,
    nitrite real,
    phosphate real,
    silicate real,
    -- JSON extra column
    extra_json text,

    -- species composition
    chemtax_prasinophytes real,
    chemtax_cryptophytes real,
    chemtax_mixed_flagellates real,
    chemtax_diatoms real,
    chemtax_haptophytes real,
    chemtax_chlorophytes real,

    --percentage of each category for this sample
    category_diatom real,
    category_phaeocystis real,
    category_dinoflagellate real,
    category_silicoflagellate real,
    category_mixed_flagellates real,
    category_other real,

    cruise text,

    tot_depth_water_col real,
    -- figure out which one is more commonly used
    chlorophyll_a_hplc real,
    primary_prod real,
    down_par real, -- check if these are mains

    -- chem/phys measurements
    pco2 real,
    diss_oxygen real,
    diss_iron real,
    diss_inorg_carbon real,
    total_alkalinity,
    diss_inorg_nitrogen real,
    diss_inorg_phosp real,
    diss_org_carbon real,
    diss_org_nitrogen real,
    part_org_carbon real,
    part_org_nitrogen real,
    tot_nitrogen real,
    tot_part_carbon real,
    tot_phosp real,
    ph real
);

create table if not exists occurrence (
    id integer primary key autoincrement,
    source_name text references source(name),
    aphia_id integer references taxonomy(aphia_id),
    latitude text,
    longitude real,
    timestamp real,
    front_zone text,
    sector text,
    depth real,
    extra_json text,
    notes text
);

create table if not exists microscopy (
    sample_id integer references sample(id),
    aphia_id integer references taxonomy(aphia_id),
    name text,
    biovolume real,
    biomass real,
    concentration real
);

create table if not exists source (
    name text primary key,
    full_reference text,
    date_accessed text,
    date_ingested text
);

create table if not exists tag (
    sample_id integer references sample(id),
    name text
);

create table if not exists taxonomy (
    aphia_id integer primary key,
    scientific_name text,
    authority text,
    superkingdom text,
    kingdom text,
    phylum text,
    subphylum text,
    superclass text,
    class text,
    subclass text,
    superorder text,
    orders text,
    suborder text,
    infraorder text,
    superfamily text,
    family text,
    genus text,
    species text,
    modified text
);