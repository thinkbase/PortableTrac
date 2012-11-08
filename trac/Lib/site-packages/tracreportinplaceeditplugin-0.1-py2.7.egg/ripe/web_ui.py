# -*- coding: utf-8 -*-
#----------------------------------------------------------------------------
# Name:         web_ui.py
# Purpose:      The TracReportInplaceEditPlugin Trac plugin handler module
#
# Author:       Richard Liao <richard.liao.i@gmail.com>
#
#----------------------------------------------------------------------------

# python modules
import os
import inspect
import time
import textwrap
import urllib

# trac modules
from trac.core import *
from trac.db import DatabaseManager
from trac.util.html import html
from trac.web.chrome import add_script, add_stylesheet
from trac.web.api import RequestDone
from trac.ticket import Ticket, TicketSystem
from trac.util import get_reporter_id

# trac interfaces for components
from trac.perm import IPermissionRequestor
from trac.web.chrome import ITemplateProvider
from trac.web import IRequestHandler
from trac.web.api import ITemplateStreamFilter

# other trac modules you may need
# from trac.web.main import IRequestFilter

# third party modules
from pkg_resources import resource_filename
import simplejson

# import plugins module
from model import schema, schema_version, RipeStore
from utils import *
from i18n_domain import gettext, _, tag_, N_, add_domain

__all__ = ['RipeModule']

class RipeModule(Component):

    implements(
                IPermissionRequestor,
                ITemplateProvider,
                IRequestHandler,
                ITemplateStreamFilter,
            )

    def __init__(self):
        locale_dir = resource_filename(__name__, 'locale')
        add_domain(self.env.path, locale_dir)

    # IPermissionRequestor methods

    def get_permission_actions(self):
        actions = ['RIPE_EDIT','RIPE_ADMIN', ]
        return actions

    # ITemplateProvider

    def get_templates_dirs(self):
        return [resource_filename(__name__, 'templates')]

    def get_htdocs_dirs(self):
        return [('ripe', resource_filename(__name__, 'htdocs'))]

    # IRequestHandler methods

    def match_request(self, req):
        return req.path_info.startswith('/ripe')


    def process_request(self, req):
        req.perm.assert_permission('RIPE_EDIT')

        data = {
            "gettext": gettext,
            "_": _,
            "tag_": tag_,
            "N_": N_,
        }

        if req.path_info.startswith('/ripe/query'):
            result = {}
            result["status"] = "1"
            result["field_infos"] = self._handle_ripe_query(req)
            jsonstr = simplejson.dumps(result)
            self._send_response(req, jsonstr)
        elif req.path_info.startswith('/ripe/save'):
            value = self._handle_ripe_save(req)
            self._send_response(req, value)

        return 'ripe.html', data, None

    ## ITemplateStreamFilter

    def filter_stream(self, req, method, filename, stream, data):
        if (filename == "report_view.html" and req.path_info.startswith("/report/")) or \
            (filename == "query.html" and req.path_info.startswith("/query")):
            if "RIPE_EDIT" in req.perm and "TICKET_MODIFY" in req.perm:
                add_stylesheet(req, 'ripe/ripe.css')
                add_script(req, 'ripe/json2.js')
                add_script(req, 'ripe/jquery.jeditable.js')
                add_script(req, 'ripe/ripe.js')

        return stream
    # internal methods
    def _handle_ripe_query(self, req):
        """ hander for query  """
        ticket = Ticket(self.env, 1)

        # {'type': 'text', 'name': 'summary', 'label': 'Summary'}
        # {'label': u'Stage', 'name': 'stage', 'order': 102, 'type': u'select', 'options':
        # [u'Todo', u'Try', u'Review', u'Blessed', u'Upcoming', u'Livin'], 'value': u'1', 'custom': True}
        # text, select, radio, textarea, time

        always_skip_fields = {
            "id": None,
            "ticket": None,
            "summary": None,
            "description": None,
            "cc": None,
            "changetime": None,
            "time": None,
            "resolution": None,
        }
        skip_fields = {}
        for field in self.config.getlist("ripe", "skip_fields", []):
            skip_fields[field] = None
        skip_fields.update(always_skip_fields)


        # get field type and options
        field_infos = {}
        for field_info in ticket.fields:
            if field_info["type"] in ["time", "textarea"]:
                continue
            if field_info["type"] == "radio":
                field_info["type"] = "select"
            if field_info["type"] == "select":
                # convert list to dict
                options = {}
                for option in field_info["options"]:
                    options[option] = option
                field_info["options"] = options
            if field_info["name"] not in skip_fields:
                field_infos[field_info["name"]] = field_info
        return field_infos

    def _handle_ripe_save(self, req):
        """ hander for save  """
        # TODO: workflow

        # get ticket id
        ticket_id = req.args.get("ticket_id")
        value = req.args.get("value", "").strip()
        field = req.args.get("field")
        old_value = req.args.get("old_value")

        # ticket
        ticket = Ticket(self.env, ticket_id)
        current_value = ticket.values.get(field)

        # validation
        if current_value != old_value and (old_value or current_value):
            self.log.info("Field value should be %s, got %s" % (repr(current_value), repr(old_value)))
            raise TracError("field value inconsistant.")

        # set params
        params = {}
        params[field] = value
        ticket.populate(params)

        # save ticket
        comment = "Updated from report"
        author = get_reporter_id(req, 'author')
        ticket.save_changes(author, comment)

        return value

    def _send_response(self, req, message):
        """ send response and stop request handling
        """
        message = isinstance(message, unicode) and message.encode("utf-8") or message
        req.send_response(200)
        req.send_header('Cache-control', 'no-cache')
        req.send_header('Expires', 'Fri, 01 Jan 1999 00:00:00 GMT')
        req.send_header('Content-Type', 'text/plain' + ';charset=utf-8')
        req.send_header('Content-Length', len(message))
        req.end_headers()

        if req.method != 'HEAD':
            req.write(message)
        raise RequestDone

