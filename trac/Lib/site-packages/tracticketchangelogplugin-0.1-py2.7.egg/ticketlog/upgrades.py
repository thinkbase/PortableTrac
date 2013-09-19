# -*- coding: utf-8 -*-
#----------------------------------------------------------------------------
# Name:         upgrades.py
# Purpose:      The TracTicketChangelogPlugin Trac plugin upgrade module
#
# Author:       Richard Liao <richard.liao.i@gmmail.com>
#
#----------------------------------------------------------------------------


"""Automated upgrades for the TracTicketChangelogPlugin database tables, and other data stored
in the Trac environment."""

def add_ticketlog_table(env, db):
    """Migrate db."""

    pass

map = {
    1: [add_ticketlog_table],
}
