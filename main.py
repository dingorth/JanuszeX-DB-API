#!/usr/bin/python3
import json
import psycopg2
import sys
import argparse

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
        connect_str = "dbname='{}' user='{}' host='{}' password='{}'".format(
            db_name, login, 'localhost', password)
        self.conn = psycopg2.connect(connect_str)

    def disconnect(self):
        self.conn.close()

    def initialize_db(self):
        with self.conn.cursor() as c:
            c.execute(open("schema.sql", "r").read())
            self.conn.commit()

    def authenticate(self, id, passwd):
        with self.conn.cursor() as c:
            c.execute("""SELECT * FROM users WHERE id = %s and passwd_h = crypt(%s, passwd_h)""",
                         (id, passwd))
            if c.rowcount == 1:
                return True
            return False

    def api_return(self, status, data=None, debug=None):
        r = { 'status' : status }
        if data != None:
            r['data'] = data
        if debug != None:
            r['debug'] = debug
        return r

    def user_exists(self, id):
        with self.conn.cursor() as c:
            c.execute("""SELECT * FROM users WHERE id = %s""", (id,))
            if c.rowcount == 1:
                return True
            return False


    ''' JanuszeX API calls begin here '''


    """open <database> <login> <password>
    przekazuje dane umożliwiające podłączenie Twojego programu do 
    bazy - nazwę bazy, login oraz hasło, wywoływane dokładnie jeden raz, w pierwszej linii wejścia
    zwraca status OK/ERROR w zależności od tego czy udało się nawiązać połączenie z bazą"""

    def open(self, args):
        try:
            self.connect(args['login'], args['password'], args['database'])
            if self.need_db_init:
                self.initialize_db()
                self.need_db_init = False
            return self.api_return("OK")
        except Exception as e:
            return self.api_return("ERROR", debug=str(e))



    """root <secret> <newpassword> <data> <emp>
    tworzy nowego pracownika o unikalnym indentyfikatorze <emp>
    z hasłem <newpassword>, jest to jedyny pracownik, który nie ma 
    przełożonego, argument <secret> musi być równy 'qwerty' 
    zwraca status OK/ERROR"""

    def root(self, args):
        try:
            if args['secret'] != 'qwerty':
                self.api_return("ERROR", debug='wrong secret')
            with self.conn.cursor() as c:
                c.execute("""INSERT INTO users(id, parent, ancestors, data, passwd_h) 
                             VALUES (%s, NULL, '{}', %s, crypt(%s, gen_salt('bf')) ) """,
                             (args['emp'], args['data'], args['newpassword']))
                self.conn.commit()
            return self.api_return("OK")
        except Exception as e:
            return self.api_return("ERROR", debug=str(e))


    """new <admin> <passwd> <data> <newpasswd> <emp1> <emp> 
    dodawanie nowego pracownika o identyfikatorze <emp> z danymi <data> i 
    hasłem dostępu <newpasswd>, pracownik <emp> staje się podwładnym pracownika <emp1>, 
    <admin> musi być pracownikiem <emp1> lub jego bezpośrednim lub pośrednim przełożonym, 
    <passwd> to hasło pracownika <admin>
    nie zwraca danych"""

    def new(self, args):
        try:
            if not self.authenticate(args['admin'], args['passwd']):
                return self.api_return("ERROR", debug="wrong password")
            
            if not self._no_auth_ancestor(args["emp1"], args["admin"], reflexive=True):
                return self.api_return("ERROR", debug="this user can't do that action")

            with self.conn.cursor() as c:
                c.execute("""INSERT INTO users(id, parent, data, passwd_h)
                             VALUES (%s, %s, %s, crypt(%s, gen_salt('bf')) )""",
                             (args['emp'], args['emp1'], args['data'] if 'data' in args else None,
                              args['newpasswd']))

            self.conn.commit()
            return self.api_return("OK")
        except Exception as e:
            return self.api_return("ERROR", debug=str(e))


    """remove <admin> <passwd> <emp>
    usuwanie pracownika <emp> wraz z wszystkimi pracownikami, 
    którzy mu (bezpośrednio lub pośrednio) podlegają. 
    <admin> musi być bezpośrednim lub pośrednim przełożonym 
    pracownika <emp> (zauważ, że oznacza to , że nie da się usunąć prezesa), 
    <passwd> to hasło pracownika <admin>
    nie zwraca danych"""

    def remove(self, args):
        try:
            if not self.authenticate(args['admin'], args['passwd']):
                return self.api_return("ERROR", debug="wrong password")

            if not self.user_exists(args['emp']):
                return self.api_return("ERROR", debug="user doesn't exists")

            if not self._no_auth_ancestor(args['emp'], args['admin']):
                return self.api_return("ERROR", debug="this user can't do that action")

            with self.conn.cursor() as c:
                c.execute("""DELETE from users where id = %s""", (args['emp'],))
                self.conn.commit()
                return self.api_return("OK")

        except Exception as e:
            return self.api_return("ERROR", debug=str(e))


    """child <admin> <passwd> <emp>
    zwraca identyfikatory wszystkich pracowników bezpośrednio podległych <emp>, 
    <admin> może być dowolnym pracownikiem,, <passwd> to hasło pracownika <admin>
    tabela data powinna zawierać kolejne wartości <emp>"""

    def child(self, args):
        try:
            if not self.authenticate(args['admin'], args['passwd']):
                return self.api_return("ERROR", debug="wrong password")
            if not self.user_exists(args['emp']):
                return self.api_return("ERROR", debug="user doesn't exists")
            with self.conn.cursor() as c:
                c.execute("""SELECT id from users where parent=%s""", (args['emp'],))
                d = list(map(lambda x:x[0], c.fetchall()))
                return self.api_return("OK", data=d)
        except Exception as e:
            return self.api_return("ERROR", debug=str(e))


    """parent <admin> <passwd> <emp> 
    zwraca identyfikator bezpośredniego przełożonego <emp>, 
    <admin> może być dowolnym pracownikiem,, <passwd> to hasło pracownika <admin>
    tabela data powinna zawierać dokładnie jedną wartość <emp>"""

    def parent(self, args):
        try:
            if not self.authenticate(args['admin'], args['passwd']):
                return self.api_return("ERROR", debug="wrong password")
            if not self.user_exists(args['emp']):
                return self.api_return("ERROR", debug="user doesn't exists")
            with self.conn.cursor() as c:
                c.execute("""SELECT parent from users where id=%s""", (args['emp'],))
                return self.api_return("OK", data=c.fetchall()[0][0])
        except Exception as e:
            return self.api_return("ERROR", debug=str(e))

    """ancestors <admin> <passwd> <emp> 
    zwraca identyfikatory wszystkich pracowników, którym <emp> pośrednio lub 
    bezpośrednio podlega, <admin> może być dowolnym pracownikiem, 
    <passwd> to hasło pracownika <admin>
    tabela data powinna zawierać kolejne wartości <emp>"""

    def ancestors(self, args):
        try:
            if not self.user_exists(args['emp']):
                return self.api_return("ERROR", debug="user doesn't exists")
            if not self.authenticate(args['admin'], args['passwd']):
                return self.api_return("ERROR", debug="wrong password")
            with self.conn.cursor() as c:
                c.execute("""SELECT get_ancestors(%s)""", (args['emp'],))
                return self.api_return("OK", data=c.fetchall()[0][0])
        except Exception as e:
            return self.api_return("ERROR", debug=str(e))


    """descendants <admin> <passwd> <emp> 
    zwraca identyfikatory wszystkich pracowników bezpośrednio lub pośrednio 
    podległych <emp>, <admin> może być dowolnym pracownikiem, 
    <passwd> to hasło pracownika <admin>
    tabela data powinna zawierać kolejne wartości <emp>"""

    def descendants(self, args):
        try:
            if not self.authenticate(args['admin'], args['passwd']):
                return self.api_return("ERROR", debug="wrogn password")
            if not self.user_exists(args['emp']):
                return self.api_return("ERROR", debug="user doesn't exists")
            with self.conn.cursor() as c:
                c.execute("""SELECT get_descendants(%s)""", (args['emp'],))
                d = list(map(lambda x:x[0], c.fetchall()))
                return self.api_return("OK", data=d)
        except Exception as e:
            self.api_return("ERROR", debug=str(e))


    def _no_auth_ancestor(self, emp1, emp2, reflexive=False):
        if emp1 == emp2 and reflexive:
            return True
        with self.conn.cursor() as c:
            c.execute("""SELECT is_ancestor(%s, %s)""", (emp1, emp2))
            return c.fetchone()[0]


    """ancestor <admin> <passwd> <emp1> <emp2> 
    sprawdza czy <emp1> bezpośrednio lub pośrednio podlega <emp2>, 
    <admin> może być dowolnym pracownikiem, <passwd> to hasło pracownika <admin>
    tabela data powinna zawierać dokładnie jedną wartość: true albo false"""

    def ancestor(self, args):
        try:
            if not self.authenticate(args['admin'], args['passwd']):
                return self.api_return("ERROR", debug="wrong password")

            if not self.user_exists(args['emp1']):
                return self.api_return("ERROR", debug="user doesn't exist")
            if not self.user_exists(args['emp2']):
                return self.api_return("ERROR", debug="user doesn't exist")

            is_ancestor = self._no_auth_ancestor(args['emp1'], args['emp2'])

            return self.api_return("OK", data=is_ancestor)
        except Exception as e:
            return self.api_return("ERROR", debug=str(e))


    """read <admin> <passwd> <emp>
    zwraca dane <data> pracownika <emp>, <admin> musi być musi być pracownikiem <emp> 
    lub bezpośrednim lub pośrednim przełożonym pracownika <emp>, 
    <passwd> to hasło pracownika <admin>
    tabela data powinna dokładnie jedną wartość <data>"""

    def read(self, args):
        try:
            if not self.authenticate(args['admin'], args['passwd']):
                return self.api_return("ERROR", debug="wrong password")

            if not self.user_exists(args['emp']):
                return self.api_return("ERROR", debug="user doesn't exists")

            if not self._no_auth_ancestor(args["emp"], args["admin"], reflexive=True):
                return self.api_return("ERROR", debug="this user can't do that action")

            with self.conn.cursor() as c:
                c.execute("""SELECT data from users where id=%s""", (args['emp'],))
                return self.api_return("OK", data=c.fetchall()[0][0])
        except Exception as e:
            return self.api_return("ERROR", debug=str(e))


    """update <admin> <passwd> <emp> <newdata>
    zmienia dane pracownika <emp> na <newdata>, 
    <admin> musi być pracownikiem <emp> lub bezpośrednim lub pośrednim 
    przełożonym pracownika <emp>, <passwd> to hasło pracownika <admin>
    nie zwraca danych"""

    def update(self, args):
        try:
            if not self.authenticate(args['admin'], args['passwd']):
                return self.api_return("ERROR", debug="wrong password")
            if not self._no_auth_ancestor(args["emp"], args["admin"], reflexive=True):
                return self.api_return("ERROR", debug="this user can't do that action")

            with self.conn.cursor() as c:
                c.execute("""UPDATE users SET data=%s WHERE id=%s""", (args['newdata'], args['emp'],))
                self.conn.commit()
                return self.api_return("OK")
        except Exception as e:
            return self.api_return("ERROR", debug="{}, {}".format(str(e), type(e)))

if __name__ == "__main__":

    parser = argparse.ArgumentParser(description='JanuszeX DB API')
    parser.add_argument('-init', action='store_true', help='initialize database', default=False)

    args = parser.parse_args()
    api = JanuszeXAPI(args.init)

    for nr, line in enumerate(sys.stdin):
        cmd = json.loads(line)
        cmd_name = list(cmd.keys())[0]
        rtn = getattr(api, cmd_name)(cmd[cmd_name]) 
        # albo rtn = api.api_call(command_type, command[command_type]) 
        print('{}: {}'.format(nr+1, rtn))
