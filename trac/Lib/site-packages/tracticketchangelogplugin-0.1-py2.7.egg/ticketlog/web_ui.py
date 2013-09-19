# -*- coding: utf-8 -*-
#----------------------------------------------------------------------------
# Name:         web_ui.py
# Purpose:      The TracTicketChangelogPlugin Trac plugin handler module
#
# Author:       Richard Liao <richard.liao.i@gmmail.com>
#
#----------------------------------------------------------------------------

# python modules
import os
import inspect
import time
import textwrap
import urllib
import re
import cgi

# trac modules
from trac.core import *
from trac.db import DatabaseManager
from trac.util.html import html
from trac.web.chrome import add_script, add_stylesheet
from trac.web.chrome import Chrome
from trac.web.api import RequestDone

# trac interfaces for components
from trac.perm import IPermissionRequestor
from trac.web.chrome import ITemplateProvider
# from trac.web.chrome import INavigationContributor
from trac.web import IRequestHandler
# from trac.admin import IAdminPanelProvider
# from trac.env import IEnvironmentSetupParticipant
from trac.web.api import ITemplateStreamFilter

# other trac modules you may need
# from trac.web.main import IRequestFilter

# third party modules
from pkg_resources import resource_filename

try:
    import simplejson
except ImportError:
    import json as simplejson

# import plugins module
from model import schema, schema_version, TicketlogStore
from utils import *
from i18n_domain import gettext, _, tag_, N_, add_domain

__all__ = ['TicketlogModule']

class TicketlogModule(Component):

    implements(
                IPermissionRequestor,
                ITemplateProvider,
                IRequestHandler,
                ITemplateStreamFilter,
                # INavigationContributor,
                # IAdminPanelProvider,
                # uncomment this line after modify model.py
                # IEnvironmentSetupParticipant,
            )

    def __init__(self):
        locale_dir = resource_filename(__name__, 'locale')
        add_domain(self.env.path, locale_dir)
        
        # detect if trac support multi repository
        sql_string = """
            SELECT * FROM repository LIMIT 1
            """
        db = self.env.get_db_cnx()
        cursor = db.cursor()
        try:
            cursor.execute(sql_string)
            self.multi_repository = True
        except:
            self.multi_repository = False
        

    # IPermissionRequestor methods

    def get_permission_actions(self):
        actions = ['TICKETLOG_VIEW', 'TICKETLOG_EDIT','TICKETLOG_ADMIN', ]
        return actions


    # ITemplateProvider

    def get_templates_dirs(self):
        return [resource_filename(__name__, 'templates')]

    def get_htdocs_dirs(self):
        return [('ticketlog', resource_filename(__name__, 'htdocs'))]


    # IRequestHandler methods

    def match_request(self, req):
        return req.path_info.startswith('/ticketlog')


    def process_request(self, req):
        req.perm.assert_permission('TICKETLOG_VIEW')

        data = {
            "gettext": gettext,
            "_": _,
            "tag_": tag_,
            "N_": N_,
        }

        if req.path_info.startswith('/ticketlog/query'):
            req.perm.assert_permission('TICKETLOG_VIEW')
            # query revisions of ticket
            result = {}
            result["status"] = "1"
            result["data"] = self._handle_ticketlog_query(req)
            jsonstr = simplejson.dumps(result)
            self._send_response(req, jsonstr)

        return 'ticketlog.html', data, None

    ## ITemplateStreamFilter

    def filter_stream(self, req, method, filename, stream, data):
        if filename == "ticket.html" and req.path_info.startswith("/ticket/"):
            if "TICKETLOG_VIEW" in req.perm:
                add_stylesheet(req, 'ticketlog/ticketlog.css')
                add_script(req, 'ticketlog/json2.js')
                add_script(req, 'ticketlog/ticketlog.js')

        return stream

    # internal methods
    def _handle_ticketlog_query(self, req):
        """ hander for query ticket revisions """
        jsonstr = urllib.unquote(req.read())
        req.args.update(simplejson.loads(jsonstr))

        # get ticket id
        ticket_id = req.args.get("ticket_id")

        # query ticket revisions
        data = {}
        data["ticket_id"] = ticket_id
        data["headers"] = [ _("Changeset"),
                            _("Author"),
                            _("Time"),
                            _("ChangeLog")]
        data["header_width"] = [ "5em",
                            "6em",
                            "8em",
                            ""]
        data["revisions"] = self._get_ticket_revisions(req, ticket_id)

        return data

    def _get_ticket_revisions(self, req, ticket_id):
        """ get ticket revisions """
        revisions = []

        if not ticket_id:
            return revisions

        db = self.env.get_db_cnx()
        cursor = db.cursor()

        sql_string_multi_repos = """
            SELECT p.value, v.rev, v.author, v.time, v.message
                FROM revision v
                LEFT JOIN repository p
                ON v.repos = p.id AND p.name='name'
                WHERE message LIKE %s
            """
        sql_string = """
            SELECT rev, author, time, message
                FROM revision
                WHERE message LIKE %s
            """
        if self.multi_repository:
            cursor.execute(sql_string_multi_repos, ["%%#%s%%" % ticket_id])
        else:
            cursor.execute(sql_string, ["%%#%s%%" % ticket_id])
            
        rows = cursor.fetchall()

        log_pattern = self.config.get("ticketlog", "log_pattern", "\s*#%s\s+.*")
        log_message_maxlength = self.config.get("ticketlog", "log_message_maxlength", None)
        p = re.compile(log_pattern % ticket_id, re.M + re.S + re.U)

        intermediate = {}
        for row in rows:
            if self.multi_repository:
                repository_name, rev, author, time, message = row
            else:
                rev, author, time, message = row

            if not p.match(message):
                continue

            if self.multi_repository:
                link = "%s/%s" % (rev, repository_name)     
                # Using (rev, author, time, message) as the key 
                # If branches from the same repo are under Trac system
                # Only one changeset will be in the ticket changelog
                intermediate[(rev, author, time, message)] = link
            else:
                intermediate[(rev, author, time, message)] = rev
            
        for key in intermediate:
            revision = {}
            revision["rev"], revision["author"], revision["time"], message = key
            if log_message_maxlength and len(message) > log_message_maxlength:
                # cut message
                message = message[:log_message_maxlength] + ' (...)'
            message = cgi.escape(message)
            revision["message"] = message
            
            revision["link"] = intermediate[key]
            revisions.append(revision)

        revisions.sort(key=lambda r: r["time"], reverse=True)
        
        def format_revision(revision):
            if revision["time"] > 2147483647:
                revision["time"] = revision["time"] / 1000000
            
            revision["time"] = format_date_full(revision["time"])
            revision["author"] = Chrome(self.env).format_author(req, revision["author"])
            return revision
        revisions = map(format_revision, revisions)

        return revisions

    def _send_response(self, req, message):
        """ send response and stop request handling
        """
        req.send_response(200)
        req.send_header('Cache-control', 'no-cache')
        req.send_header('Expires', 'Fri, 01 Jan 1999 00:00:00 GMT')
        req.send_header('Content-Type', 'text/plain' + ';charset=utf-8')
        req.send_header('Content-Length', len(isinstance(message, unicode) and message.encode("utf-8") or message))
        req.end_headers()

        if req.method != 'HEAD':
            req.write(message)
        raise RequestDone

