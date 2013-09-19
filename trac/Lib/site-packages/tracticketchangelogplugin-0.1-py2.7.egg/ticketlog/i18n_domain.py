# -*- coding: utf-8 -*-
#----------------------------------------------------------------------------
# Name:         i18n_domain.py
# Purpose:      The TracTicketChangelogPlugin Trac plugin i18n_domain module
#
# Author:       Richard Liao <richard.liao.i@gmmail.com>
#
#----------------------------------------------------------------------------

try:
    from trac.util.translation import domain_functions
    gettext, _, tag_, N_, add_domain = domain_functions('ticketlog', 
    'gettext', '_', 'tag_', 'N_', 'add_domain')
except ImportError:
    # ignore domain functions
    def add_domain(*args, **kwargs): pass
    try:
        from trac.util.translation import _, tag_, N_, gettext
    except ImportError:
        # skip support i18n, to work in trac 0.11
        def gettext(string, **kwargs): return string
        def _(string, **kwargs): return string
        def tag_(string, **kwargs): return string
        def N_(string, **kwargs): return string
    