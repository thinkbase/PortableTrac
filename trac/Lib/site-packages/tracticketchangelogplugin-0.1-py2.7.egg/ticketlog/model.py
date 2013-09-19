# -*- coding: utf-8 -*-
#----------------------------------------------------------------------------
# Name:         model.py
# Purpose:      The TracTicketChangelogPlugin Trac plugin db model module
#
# Author:       Richard Liao <richard.liao.i@gmmail.com>
#
#----------------------------------------------------------------------------

"""Model classes for objects persisted in the database."""

from trac.db import Table, Column, Index

class TicketlogStore(object):
    """Represents a table."""

    _schema = [
        Table('ticketlog_store', key='id')[
            Column('id', auto_increment=True),
            Column('col1'),
            Index(['col1'])
        ]
    ]

    def __init__(self, env, col1=None):
        """Initialize a new entry with the specified attributes.

        To actually create this build log in the database, the `insert` method
        needs to be called.
        """
        self.env = env
        self.id = None
        self.col1 = col1

    def delete(cls, env, col1, db=None):
        """Remove the col1 from the database."""
        if not db:
            db = env.get_db_cnx()
            handle_ta = True
        else:
            handle_ta = False

        cursor = db.cursor()
        cursor.execute("DELETE FROM ticketlog_store WHERE col1=%s;", (col1,))

        if handle_ta:
            db.commit()

    delete = classmethod(delete)

    def insert(cls, env, col1, db=None):
        """Insert a new col1 into the database."""
        if not db:
            db = env.get_db_cnx()
            handle_ta = True
        else:
            handle_ta = False

        cursor = db.cursor()
        cursor.execute("INSERT INTO ticketlog_store (col1, ) VALUES (%s,);",
                       (col1, ))
        id = db.get_last_id(cursor, 'ticketlog_store')

        if handle_ta:
            db.commit()

        return id

    insert = classmethod(insert)

    def get(cls, env, db=None):
        """Retrieve from the database that match
        the specified criteria.
        """
        if not db:
            db = env.get_db_cnx()

        cursor = db.cursor()

        cursor.execute("SELECT col1 FROM ticketlog_store ORDER BY col1;")

        return [m[0] for m in cursor.fetchall()]

    get = classmethod(get)


schema = TicketlogStore._schema
schema_version = 1
