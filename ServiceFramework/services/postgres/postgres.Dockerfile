FROM postgres:14.4
COPY init.sql /docker-entrypoint-initdb.d/