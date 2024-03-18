-- total database rows
select count(*) from sample;

-- multiple filters on full dataset
select *
from sample
where cryptophytes < 0.5 and latitude > -67.0 and latitude < -60.0 and prasinophytes > 0.1;

-- find amount of entries per month of year
select count(*) as entries, strftime('%Y-%m', timestamp) as year_month
from sample
group by year_month
order by year_month asc;

-- amount of every genus
select count(*) as entries, genus
from sample, microscopy
where sample.aphia_id = microscopy.aphia_id
group by genus
order by entries desc;

-- average salinity from certain region
select avg(salinity)
from sample
where latitude > -67 and latitude < -60;

select *
from sample
where latitude > 0;

select * from sample where scientific_name is not null;

analyze sample;

update sample set aphia_id = micro.aphia
from (select aphia_id as aphia, scientific_name as sci_name from microscopy) as micro where sample.scientific_name = micro.sci_name;

select s.scientific_name, m.aphia_id from sample as s, microscopy as m where s.scientific_name = m.scientific_name;

update sample
set aphia_id = (select aphia_id from microscopy where sample.scientific_name = microscopy.scientific_name);

select * from sample where aphia_id is not null limit 50;

select * from microscopy where aphia_id = 248106;