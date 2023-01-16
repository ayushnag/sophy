create table if not exists sample (
    id integer primary key autoincrement,
    source_name text references source(name),
    cruise text,

    -- location(s) and time
    latitude real,
    longitude real,
    timestamp text,
    front_zone text,
    sector text,

    -- species composition
    percent_phaeo real,
    percent_diatom real,
    percent_other real,

    -- chem/phys variables
    depth real,
    chl_a real,
    salinity real,
    temperature real,
    mld real,
    par real,
    nitrate real,
    nitrite real,
    phosphate real,
    silicate real,
    -- JSON extra column
    extra_json text
);

create table if not exists occurrence (
    id integer primary key autoincrement,
    source_name text references source(name),
    aphia_id integer references taxonomy(aphia_id),
    name text,
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