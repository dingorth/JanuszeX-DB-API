-- student database already exists
-- init user already exists

-- CREATE EXTENSION pgcrypto;

REVOKE ALL PRIVILEGES ON TABLE users FROM app;
REVOKE ALL PRIVILEGES ON DATABASE student FROM app;
DROP USER IF EXISTS app;
DROP TABLE IF EXISTS users;

CREATE TABLE users(
    id int primary key not null, 
    parent int references users(id) on delete cascade,
    ancestors int[] not null,
    data varchar(100), 
    passwd_h text not null
);
-- root node should have empty ancestors and NULL parent
-- ancestor and descendant relations are not reflexive

CREATE USER app WITH ENCRYPTED PASSWORD 'qwerty';
GRANT CONNECT ON DATABASE student to app;
GRANT SELECT, INSERT, UPDATE, DELETE, REFERENCES ON TABLE users TO app; -- may want to delete REFERENCES




-- FUNCTIONS

CREATE OR REPLACE FUNCTION get_ancestors(int) RETURNS int[] AS
$X$
	select ancestors from users where id=$1;
$X$ LANGUAGE SQL STABLE;

-- czy $1 podlega $2
CREATE OR REPLACE FUNCTION is_ancestor(int,int) RETURNS boolean AS
$X$
	select array_append(get_ancestors($1), $1)  @> array_append(get_ancestors($2), $2) and $1 <> $2;
$X$ LANGUAGE SQL STABLE;


CREATE OR REPLACE FUNCTION get_descendants(int) RETURNS SETOF int AS 
$X$
	select id from users where is_ancestor(id, $1);
$X$ LANGUAGE SQL STABLE;



-- TRIGGERS

-- Don't execute on root node.
CREATE OR REPLACE FUNCTION update_ancestors() RETURNS TRIGGER AS
$X$
BEGIN
	NEW.ancestors := array_append(get_ancestors(NEW.parent), NEW.parent);
	RETURN NEW;
END
$X$ LANGUAGE plpgsql;


CREATE TRIGGER on_insert_to_users BEFORE INSERT ON users
FOR EACH ROW WHEN (NEW.parent is not NULL) EXECUTE PROCEDURE update_ancestors();
