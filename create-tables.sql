PRAGMA foreign_keys = ON;
CREATE TABLE sample (
    id integer primary key autoincrement,
    latitude float,
    longitude float,
    timestamp datetime,
    depth float,
    pressure float,
    tot_depth_water_col float,
    source_name varchar references source (name),
    aphia_id int references microscopy (aphia_id),
    region varchar references location (region),

    salinity float,
    temperature float,
    density float,
    chlorophyll float,
    phaeopigments float,
    fluorescence float,
    primary_prod float,
    cruise varchar,

    down_par float,
    light_intensity float,

    prasinophytes float,
    cryptophytes float,
    mixed_flagellates float,
    diatoms float,
    haptophytes float,

    nitrate float,
    nitrite float,
    pco2 float,
    diss_oxygen float,
    diss_inorg_carbon float,
    diss_inorg_nitrogen float,
    diss_inorg_phosp float,
    diss_org_carbon float,
    diss_org_nitrogen float,
    part_org_carbon float,
    part_org_nitrogen float,
    org_carbon float,
    org_matter float,
    org_nitrogen float,
    phosphate float,
    silicate float,
    tot_nitrogen float,
    tot_part_carbon float,
    tot_phosp float,
    ph float,

    origin_id varchar,
    strain varchar,
    notes varchar
);

CREATE TABLE extra (
    sample_id integer references sample (id),
    key varchar,
    value varchar
);

CREATE TABLE source (
    name varchar primary key,
    author varchar,
    doi varchar,
    url varchar,
    date_accessed datetime,
    date_ingested datetime
);

CREATE TABLE tag (
    sample_id integer references sample (id),
    name varchar
);

CREATE TABLE location (
    region varchar primary key,
    ice_regime varchar
);

CREATE TABLE microscopy (
    aphia_id integer primary key,
    scientific_name varchar,
    superkingdom varchar,
    kingdom varchar,
    phylum varchar,
    subphylum varchar,
    superclass varchar,
    class varchar,
    subclass varchar,
    superorder varchar,
    "order" varchar,
    suborder varchar,
    infraorder varchar,
    superfamily varchar,
    family varchar,
    genus varchar,
    species varchar,
    citation varchar,
    modified datetime
);