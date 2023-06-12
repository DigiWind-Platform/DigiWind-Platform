/*CREATE USER fivedit;
ALTER USER fivedit WITH PASSWORD 'password';

CREATE DATABASE sensors;
GRANT ALL PRIVILEGES ON DATABASE sensors TO fivedit;*/

CREATE TABLE datatable (
	time timestamp NOT NULL,
	PRIMARY KEY (time)
);
