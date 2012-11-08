# -*- coding: utf-8 -*-
#----------------------------------------------------------------------------
# Name:         upgrades.py
# Purpose:      The TracReportInplaceEditPlugin Trac plugin upgrade module
#
# Author:       Richard Liao <richard.liao.i@gmail.com>
#
#----------------------------------------------------------------------------


"""Automated upgrades for the TracReportInplaceEditPlugin database tables, and other data stored
in the Trac environment."""

def add_ripe_table(env, db):
    """Migrate db."""

    pass

map = {
    1: [add_ripe_table],
}
