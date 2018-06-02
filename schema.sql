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
    root_path int[] not null,
    data text, 
    passwd_h text not null
);

CREATE USER app WITH ENCRYPTED PASSWORD 'qwerty';
GRANT CONNECT ON DATABASE student to app;
GRANT SELECT, INSERT, UPDATE, REFERENCES ON TABLE users TO app;


-- FUNCTIONS

-- get root path of user with specified id
CREATE OR REPLACE FUNCTION get_root_path(int) RETURNS int[] AS
$X$
	select root_path from users where id=$1;
$X$ LANGUAGE SQL STABLE;





-- TRIGGERS

-- Don't execute on root node.
-- Root node shouldn't have root_path empty
-- but should have NULL parent
CREATE OR REPLACE FUNCTION update_root_path() RETURNS TRIGGER AS
$X$
BEGIN
	NEW.root_path := array_append(get_root_path(NEW.parent), NEW.id);
	RETURN NEW;
END
$X$ LANGUAGE plpgsql;


CREATE TRIGGER on_insert_to_users BEFORE INSERT ON users
FOR EACH ROW WHEN (NEW.parent is not NULL) EXECUTE PROCEDURE update_root_path();
