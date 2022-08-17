create table if not exists sample (
    id integer primary key autoincrement,
    source_name text references source(name),
    aphia_id int references species(aphia_id),

    latitude real,
    longitude real,
    timestamp text,

    front_zone text,
    sector text,

    depth real,
    pressure real,
    tot_depth_water_col real,

    salinity real,
    temperature real,
    density real,
    chlorophyll real,
    phaeopigments real,
    fluorescence real,
    primary_prod real,
    cruise text,

    down_par real,
    light_intensity real,
    light_transmission real,
    mld real,

    scientific_name text,
    prasinophytes real,
    cryptophytes real,
    mixed_flagellates real,
    diatoms real,
    haptophytes real,

    nitrate real,
    nitrite real,
    pco2 real,
    diss_oxygen real,
    diss_inorg_carbon real,
    diss_inorg_nitrogen real,
    diss_inorg_phosp real,
    diss_org_carbon real,
    diss_org_nitrogen real,
    part_org_carbon real,
    part_org_nitrogen real,
    org_carbon real,
    org_matter real,
    org_nitrogen real,
    phosphate real,
    silicate real,
    tot_nitrogen real,
    tot_part_carbon real,
    tot_phosp real,
    ph real,

    origin_id text,
    strain text,
    notes text
);

create table if not exists occurrence (
    id integer primary key autoincrement,
    aphia_id integer references species(aphia_id),
    latitude text,
    longitude real,
    timestamp real,
    depth real,
    notes text
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
    superkingdom text,
    kingdom text,
    phylum text,
    subphylum text,
    superclass text,
    class text,
    subclass text,
    superorder text,
    t_order text,
    suborder text,
    infraorder text,
    superfamily text,
    family text,
    genus text,
    species text,
    modified text
);