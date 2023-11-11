create table if not exists sample (
    id integer primary key autoincrement,
    source_name text,
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
    chemtax_prasinophytes real,
    chemtax_cryptophytes real,
    chemtax_chlorophytes real,
    chemtax_mixed_flagellates real,
    chemtax_diatoms real,
    chemtax_haptophytes real,

    -- chem/phys variables
    depth real,
    chl_a real,
    salinity real,
    temperature real,
    part_org_carbon real,
    oxygen real,
    mld real,
    par real,
    nitrate real,
    nitrite real,
    phosphate real,
    silicate real,
    -- JSON extra column
    extra_json text
);

-- occurence only data
create table if not exists occurrence (
    id integer primary key autoincrement,
    source_name text,
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

-- additional microscopy data along with sample
create table if not exists microscopy (
    sample_id integer references sample(id),
    aphia_id integer references taxonomy(aphia_id),
    name text,
    biovolume real,
    biomass real,
    concentration real
);

create table if not exists tag (
    sample_id integer references sample(id),
    name text
);

-- full taxonomy of species
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
    order_ text,
    suborder text,
    infraorder text,
    superfamily text,
    family text,
    genus text,
    species text,
    modified text
);