PRAGMA foreign_keys = ON;
CREATE TABLE sample(
   id integer primary key autoincrement,
   latitude float,
   longitude float,
   source_id int,
   taxa_id int,
   cruise_id int,
   location_id int,
   origin_id varchar,
   notes varchar,
   salinity float,
   temperature float,
   density float,
   chlorophyll float,
   phaeopigments float,
   fluorescence float,
   primary_prod float,
   down_par float,
   light_intensity float,
   nitrate float,
   nitrite float,
   pco2 float,
   diss_oxygen float,
   diss_inorg_carbon float,
   diss_inorg_nitrogen float,
   diss_inorg_phosp float,
   diss_org_carbon float,
   diss_org_nitrogen float,
   part_org_carb float,
   part_org_nitrogen float,
   org_carb float,
   org_matter float,
   org_nitrogen float,
   phosphate float,
   silicate float,
   tot_nitrogen float,
   tot_part_carb float,
   tot_phosp float,
   ph float,
   foreign key(source_id) references source(id),
   foreign key(taxa_id) references taxa(id),
   foreign key(cruise_id) references cruise(id),
   foreign key(location_id) references location(id)
);

CREATE TABLE extra(
    sample_id int,
    key varchar,
    value varchar,
    foreign key(sample_id) references sample(id)
);

CREATE TABLE source(
    id integer primary key autoincrement,
    name varchar,
    author varchar,
    doi varchar,
    url varchar,
    date_accessed datetime,
    date_ingested datetime
);

CREATE TABLE tag(
    id integer primary key autoincrement,
    name varchar
);

CREATE TABLE sample_tag(
    sample_id int,
    tag_id int,
    foreign key(sample_id) references sample(id),
    foreign key(tag_id) references tag(id)
);

CREATE TABLE location(
    id integer primary key autoincrement,
    region varchar,
    ice_regime varchar
);

CREATE TABLE cruise(
    id integer primary key autoincrement,
    name varchar
);

CREATE TABLE taxa(
    id integer primary key autoincrement
);

CREATE TABLE pigment(
    id int references taxa(id),
    prasinophytes float,
    cryptophytes float,
    mixed_flagellates float,
    diatoms float,
    haptophytes float
    -- add rest
);