CREATE DATABASE gscusers;

DROP TABLE users;

USE gscusers;

CREATE TABLE users (
uid SERIAL PRIMARY KEY,
firstname VARCHAR(100) not null,
lastname VARCHAR(100) not null,
email VARCHAR(120) not null unique,
pwdhash VARCHAR(100) not null
);

SELECT * FROM users;

INSERT INTO  users (firstname, lastname, email, pwdhash) 
	VALUES ('Jaime', 'Marcos','jaimemarcos@gmail.com', 'ErtdfgcvB1');
    
SELECT * FROM users;

CREATE TABLE authorization (
email VARCHAR(120) PRIMARY KEY,
project_key VARCHAR(100) not null,
api_key VARCHAR(100) not null,
brand_queries VARCHAR(300) not null
);


SELECT * FROM authorization;


SELECT * FROM authorization;


    
