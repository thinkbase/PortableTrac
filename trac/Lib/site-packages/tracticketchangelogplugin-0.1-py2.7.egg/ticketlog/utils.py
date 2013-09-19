# -*- coding: utf-8 -*-
#----------------------------------------------------------------------------
# Name:         utils.py
# Purpose:      The TracTicketChangelogPlugin utils module
#
# Author:       Richard Liao <richard.liao.i@gmmail.com>
#
#----------------------------------------------------------------------------

import time


def get_date_from_str(date_str):
    """ convert 2008-01-01 to int
    """
    formats = [
        "%Y-%m-%d",
        "%Y/%m/%d",
        "%Y.%m.%d",
        "%Y%m%d",
        "%y-%m-%d",
        "%y/%m/%d",
        "%y.%m.%d",
        "%y%m%d",
        "%m/%d/%Y",
    ]

    timeTuple = None
    for format in formats:
        try:
            timeTuple = time.strptime(date_str, format)
            return int(time.mktime(timeTuple))
        except:
            continue
    if not timeTuple:
        return None

def format_date_full(t):
    """ convert int to 2008-01-01
    """
    try:
        t = int(float(t))
    except:
        return ""
    return time.strftime("%Y-%m-%d", time.localtime(t))

def format_time_full(t):
    try:
        t = int(t)
    except:
        return ""
    return time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(t))

def format_date_compact(t):
    return time.strftime("%y%m%d", time.localtime(t))


def format_week(t):
    return time.strftime("%Y-%W-%w", time.localtime(t))
