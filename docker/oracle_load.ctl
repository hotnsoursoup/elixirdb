LOAD DATA
INFILE '/opt/oracle/scripts/test_data.csv'
REPLACE
INTO TABLE test_data
FIELDS TERMINATED BY ',' OPTIONALLY ENCLOSED BY '"'
(id, name, dob DATE "YYYY-MM-DD", uuid)