CREATE DATABASE gscusers;

USE gscusers;

CREATE TABLE users (
uid SERIAL PRIMARY KEY,
fistname VARCHAR(100) not null,
lastname VARCHAR(100) not null,
email VARCHAR(120) not null unique,
pwdash VARCHAR(100) not null
);

SELECT * FROM users;

INSERT INTO  users (fistname, lastname, email, pwdash) 
	VALUES ('Jaime', 'Marcos','jaimemarcos@gmail.com', 'ErtdfgcvB1');
    
SELECT * FROM users;


    
