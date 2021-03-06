create table if not exists sample (
    id integer primary key autoincrement,
    latitude float,
    longitude float,
    timestamp text,
    depth float,
    front_zone,
    pressure float,
    tot_depth_water_col float,
    source_name text references source (name),
    aphia_id int references microscopy (aphia_id),
    region text references location (region),

    salinity float,
    temperature float,
    density float,
    chlorophyll float,
    phaeopigments float,
    fluorescence float,
    primary_prod float,
    cruise text,

    down_par float,
    light_intensity float,
    mld float,
    xld float,

    scientific_name text,
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

    origin_id text,
    strain text,
    notes text
);

create table if not exists extra (
    sample_id integer references sample (id),
    key text,
    value text
);

create table if not exists source (
    name text primary key,
    author text,
    doi text,
    url text,
    date_accessed text,
    date_ingested text
);

create table if not exists tag (
    sample_id integer references sample (id),
    name text
);

create table if not exists microscopy (
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