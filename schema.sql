-- Wykonaj caly ten plik przy tworzeniu bazy.
-- student database already exists
-- init user already exists

-- https://www.postgresql.org/docs/9.1/static/functions-array.html
-- array contains, is contained by

-- CREATE EXTENSION pgcrypto;

REVOKE ALL PRIVILEGES ON TABLE users FROM app;
REVOKE ALL PRIVILEGES ON DATABASE student FROM app;
DROP USER IF EXISTS app;
DROP TABLE IF EXISTS users;

CREATE TABLE users(
    id int primary key not null, 
    parent int references users(id) on delete cascade,
    root_path int[],
    data text, 
    passwd_h text not null
);

CREATE USER app WITH ENCRYPTED PASSWORD 'qwerty';
GRANT CONNECT ON DATABASE student to app;
GRANT SELECT, INSERT, UPDATE, REFERENCES ON TABLE users TO app;


-- FUNCTIONS

-- ancestors




-- TRIGGERS
-- CZY TO MA BYĆ TRIGGER CZY MOŻE FUNKCJA JAKO DEFAULT VALUE ????
-- on insert to users update root_path
CREATE OR REPLACE FUNCTION update_root_path() RETURNS TRIGGER AS
$X$
DECLARE
	parent_root_path int[]
BEGIN
	-- uwaga na roota
	select root_path into parent_root_path from users where NEW.parent=id;



	RETURN NEW;
END
$X$ LANGUAGE plpgsql;


CREATE TRIGGER on_insert_to_users AFTER INSERT ON users
FOR EACH ROW EXECUTE PROCEDURE update_root_path();
