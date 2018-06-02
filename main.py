#!/usr/bin/python3
import json
import psycopg2
import sys
import argparse

# czy potrzebne?
import secrets
import hashlib
import codecs

# https://www.digitalocean.com/community/tutorials/how-to-install-and-use-postgresql-on-ubuntu-16-04
# http://www.davejsaunders.com/2016/11/10/user-authentication-with-postgres.html
# https://www.meetspaceapp.com/2016/04/12/passwords-postgresql-pgcrypto.html
# https://x-team.com/blog/storing-secure-passwords-with-postgresql/
'''
Two users:
    - init: 
        * can modify DB schema
    - app:
        * cannot modify DB schema
        * can only modify data (INSERT, UPDATE, DELETE, SELECT)
'''

class JanuszeXAPI:
    conn = None
    need_db_init = False

    def __init__(self, need_db_init=False):
        self.need_db_init = need_db_init

    def api_call(self, name, args):
        return getattr(self, name)(args)

    def connect(self, login, password, db_name):
        try:
            # jesli user jest "init" to chyba jest to pierwsze uruchomienie
            connect_str = "dbname='{}' user='{}' host='{}' password='{}'" \
                .format(db_name, login, 'localhost', password)
            self.conn = psycopg2.connect(connect_str)
        except Exception as e:
            print(e)

    def disconnect(self):
        self.conn.close()

    def initialize_db(self):
        with self.conn.cursor() as c:
            c.execute(open("schema.sql", "r").read())
            self.conn.commit()

    def authenticate(self, login, password):
        # SELECT * FROM users WHERE email = lower('nick@example.com') AND password = crypt('12345', password);
        with self.conn.cursor() as c:
            pass
        return False

    def api_return(self, status, data=None):
        r = { 'status' : status }
        if data == None:
            return  r
        r['data'] = data
        return r

    ''' JanuszeX API calls begin here '''

    def open(self, args):
        self.connect(args['login'], args['password'], args['baza'])
        if self.need_db_init:
            self.initialize_db()
            self.need_db_init = False
        return self.api_return("OK")


    def root(self, args):
        with self.conn.cursor() as c:
            a = "INSERT INTO users(id, parent,root_path,data, passwd_hash, salt) VALUES (0, NULL, '', 'lubie placki', 'qwerty' ,'abc');"
            c.execute(a)
            self.conn.commit()
        return self.api_return("OK")

    def new(self, args):
        # INSERT INTO users (email, password) VALUES ('nick@example.com', crypt('12345', gen_salt('bf', 8)));
        with self.conn.cursor() as c:
            pass
        return self.api_return("OK")

    def remove(self, args):
        return self.api_return("OK")

    def child(self, args):
        return self.api_return("OK")

    def parent(self, args):
        return self.api_return("OK")

    def ancestors(self, args):
        return self.api_return("OK")

    def descendants(self, args):
        return self.api_return("OK")

    def ancestor(self, args):
        return self.api_return("OK")

    def read(self, args):
        return self.api_return("OK")

    def update(self, args):
        return self.api_return("OK")

if __name__ == "__main__":

    parser = argparse.ArgumentParser(description='JanuszeX DB API')
    parser.add_argument('-init', action='store_true', help='initialize database', default=False)

    args = parser.parse_args()
    api = JanuszeXAPI(args.init)

    for line in sys.stdin:
        cmd = json.loads(line)
        cmd_name = list(cmd.keys())[0]
        rtn = getattr(api, cmd_name)(cmd[cmd_name]) # albo rtn = api.api_call(command_type, command[command_type]) 
        print(rtn)
