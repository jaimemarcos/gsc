
CREATE DATABASE IF NOT EXISTS gscusers;

USE gscusers;

CREATE TABLE users (
uid INT PRIMARY KEY AUTO_INCREMENT,
firstname VARCHAR(100) not null,
lastname VARCHAR(100) not null,
email VARCHAR(120) not null unique,
pwdhash VARCHAR(100) not null
);


CREATE TABLE authorization (
email VARCHAR(120) PRIMARY KEY not null,
project_key VARCHAR(100) not null,
api_key VARCHAR(100) not null
);

SELECT * FROM authorization;

CREATE TABLE property (
search_property VARCHAR(120) PRIMARY KEY unique,
brand_queries VARCHAR(300) not null,
email VARCHAR(120) not null
);