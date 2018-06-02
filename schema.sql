-- Wykonaj caly ten plik przy tworzeniu bazy.
-- student database already exists
-- init user already exists

REVOKE ALL PRIVILEGES ON DATABASE student FROM app;
REVOKE ALL PRIVILEGES ON TABLE users FROM app;
DROP USER IF EXISTS app;
DROP TABLE IF EXISTS users;



CREATE TABLE users(
    id bigint primary key not null, 
    parent bigint, -- prezez nie ma parent. sam może być swoim parentem, albo może mieć NULL
    root_path text, -- dot separated employess id
    data text, 
    passwd_hash varchar(64), -- sha256
    salt varchar(32) -- 16 bytes random string
);

CREATE USER app WITH ENCRYPTED PASSWORD 'qwerty';
GRANT CONNECT ON DATABASE student to app;
GRANT SELECT, INSERT, UPDATE, REFERENCES ON TABLE users TO app;