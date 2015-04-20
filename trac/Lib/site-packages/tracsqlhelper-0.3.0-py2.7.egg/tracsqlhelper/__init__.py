# -*- coding: utf-8 -*-
#
# Copyright (C) 2009 Jeff Hammel <jhammel@openplans.org>
# All rights reserved.
#
# This software is licensed as described in the file COPYING, which
# you should have received as part of this distribution.
#

# XXX important -- see http://trac-hacks.org/attachment/ticket/7262

from trac.db import DatabaseManager

class SQLHelper(object):

    def actions(self, cur):
        """do actions once you have execute the SQL"""
        return {}

    def return_values(self, **kw):
        """return values from the SQL"""

    def __call__(self, env, sql, *params):
        with env.db_transaction as db:
            try:
                cursor = db.cursor()
                cursor.execute(sql, params)
                _data = self.actions(cursor)
            except Exception, e:
                env.log.error("""There was a problem executing sql:%s
    with parameters:%s
    Exception:%s""" %(sql, params, e))
                raise
        return self.return_values(**_data)

execute_non_query = SQLHelper()

class SQLGetAll(SQLHelper):
    def actions(self, cur):
        return dict(data=cur.fetchall(), desc=cur.description) 

    def return_values(self, **kw):
        return (kw.get('desc'), kw.get('data'))

get_all = SQLGetAll()

def get_all_dict(env, sql, *params):
    """Executes the query and returns a Result Set"""
    desc, rows = get_all(env, sql, *params);
    if not desc:
        return []

    results = []
    for row in rows:
        row_dict = {}
        for field, col in zip(row, desc):
            row_dict[col[0]] = field
        results.append(row_dict)
    return results

class SQLGetFirstRow(SQLHelper):
    def actions(self, cur):
        return dict(data=cur.fetchone())
    def return_values(self, **kw):
        return kw.get('data')

get_first_row = SQLGetFirstRow()

def get_scalar(env, sql, col=0, *params):
    """
    Gets a single value (in the specified column) 
    from the result set of the query
    """
    data = get_first_row(env, sql, *params)
    if data:
        return data[col]

class SQLGetColumn(SQLHelper):
    def actions(self, cur):
        data = cur.fetchall()
        return dict(data=[datum[0] for datum in data])
    def return_values(self, **kw):
        return kw.get('data')
    def __call__(self, env, table, column, where=None):
        sql = "select %s from %s" % (column, table)
        if where:
            sql += " where %s" % where
        return SQLHelper.__call__(self, env, sql)

get_column = SQLGetColumn()

def get_table(env, table):
    return get_all_dict(env, "SELECT * FROM %s" % table)

def create_table(env, table):
    """
    create a table given a component
    """

    db_connector, _ = DatabaseManager(env)._get_connector()
    stmts = db_connector.to_sql(table)
    for stmt in stmts:
        execute_non_query(env, stmt)

def insert_row_from_dict(env, table, dictionary):
    items = dictionary.items()
    # XXX this might be slightly retarded
    keys = [str(item[0]) for item in items]
#    values = ["'%s'" % str(item[1]) for item in items]
    values = [item[1] for item in items]
    sql = "INSERT INTO %s (%s) VALUES (%s)"
    sql = sql % ( table, ','.join(keys), ','.join(['%s' for v in values]))
    execute_non_query(env, sql, *values)

def update_row_from_dict(env, table, key, value, dictionary):
    items = dictionary.items()
    # XXX this might be slightly retarded
    sql = "UPDATE %s SET %s WHERE %s='%s'"
    sql = sql % ( table, 
                  ', '.join(["%s='%s'" % (item[0], item[1]) 
                             for item in items]),
                  key, 
                  value)
    execute_non_query(env, sql)
    

def insert_update(env, table, key, value, items=None):
    if items is None:
        items = {}
    if get_first_row(env, "SELECT * FROM %s WHERE %s=%s" % (table, key, '%s'), value):
        update_row_from_dict(env, table, key, value, items)
    else:
        items[key] = value
        insert_row_from_dict(env, table, items)

def columns(env, table):
    all = get_all_dict(env, "SELECT * FROM %s LIMIT 1" % table)
    assert all, 'NEED AT LEAST ONE ROW!  IF I KNEW SQL BETTER THEN I COULD PROBABLY GET AROUND THIS!'
    return all[0].keys()

def column_type(env, table, column):
    """returns type of the column in the table"""
    row = get_all_dict(env, "SELECT * FROM %s LIMIT 1" % table)
    assert row
    row = row[0]
    assert column in row
    return type(row[column])

def column_repr(env, table, column, value):
    """returns SQL repr for the column in a table"""
    reprs = { unicode: "'%s'",
              str: "'%s'",
              int: "%d"
              }
    _type = column_type(env, table, column)
    repr = reprs.get(_type, "%s")
    return repr % value
    
