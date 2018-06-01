-- Wykonaj caly ten plik przy tworzeniu bazy.

CREATE TABLE users(
    id serial, 
    parent bigint, 
    root_path text, -- string id pracownikow od tego pracodnika do roota
    data text, 
    passwd_hash varchar(64), -- sha256
    salt varchar(32) -- 16 bytes random string
);

