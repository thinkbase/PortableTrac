# -*- coding: utf-8 -*-
#
# Copyright (C) 2008-2009 Jeff Hammel <jhammel@openplans.org>
# Copyright (C) 2012 Ryan J Ollos <ryan.j.ollos@gmail.com>
#
# This software is licensed as described in the file COPYING, which
# you should have received as part of this distribution.

from trac.core import Component, implements
from trac.config import ListOption
from trac.web.api import IRequestFilter, IRequestHandler
from trac.web.chrome import (
    Chrome, ITemplateProvider, ITemplateStreamFilter, add_script,
    add_stylesheet
)

import fnmatch

USER=0; NAME=1; EMAIL=2 # indices

class AutocompleteUsers(Component):

    implements(IRequestFilter, IRequestHandler,
               ITemplateProvider, ITemplateStreamFilter)

    selectfields = ListOption('autocomplete', 'fields', default='',
                              doc='select fields to transform to autocomplete text boxes')

    # IRequestHandler methods

    def match_request(self, req):
        return req.path_info.rstrip('/') == '/subjects'

    def process_request(self, req):

        subjects = []
        if req.args.get('users', '1') == '1':
            users = self._get_users(req)
            subjects = ['%s|%s|%s' % (user[USER],
                                      user[EMAIL] and '&lt;%s&gt; ' % user[EMAIL] or '',
                                      user[NAME])
                        for value, user in users] # value unused (placeholder needed for sorting)

        if req.args.get('groups'):
            groups = self._get_groups(req)
            if groups:
                subjects.extend(['%s||group' % group for group in groups])

        req.send('\n'.join(subjects).encode('utf-8'), 'text/plain')

    # ITemplateProvider methods

    def get_htdocs_dirs(self):
        from pkg_resources import resource_filename
        return [('autocomplete', resource_filename(__name__, 'htdocs'))]

    def get_templates_dirs(self):
        return []

    # IRequestFilter methods

    def pre_process_request(self, req, handler):
        return handler

    def post_process_request(self, req, template, data, content_type):
        if template in ('ticket.html', 'admin_perms.html', 'query.html'):
            add_stylesheet(req, 'autocomplete/css/autocomplete.css')
            add_script(req, 'autocomplete/js/autocomplete.js')
            add_script(req, 'autocomplete/js/format_item.js')
            if template == 'ticket.html':
                restrict_owner = self.env.config.getbool('ticket', 'restrict_owner')
                if req.path_info.rstrip() == '/newticket':
                    add_script(req, 'autocomplete/js/autocomplete_newticket_cc.js')
                    if not restrict_owner:
                        add_script(req, 'autocomplete/js/autocomplete_newticket.js')
                else:
                    add_script(req, 'autocomplete/js/autocomplete_ticket_cc.js')
                    if not restrict_owner:
                        add_script(req, 'autocomplete/js/autocomplete_ticket.js')
            elif template == 'admin_perms.html':
                add_script(req, 'autocomplete/js/autocomplete_perms.js')
            elif template == 'query.html':
                add_script(req, 'autocomplete/js/autocomplete_query.js')
            
        return template, data, content_type

    # ITemplateStreamFilter methods

    def filter_stream(self, req, method, filename, stream, data):
        if filename == 'ticket.html':
            fields = [field['name'] for field in data['ticket'].fields 
                      if field['type'] == 'select']
            fields = set(sum([fnmatch.filter(fields, pattern)
                              for pattern in self.selectfields], []))
            
        return stream
    
    # Private methods
    
    def _get_groups(self, req):
        # Returns a list of groups by filtering users with session data
        # from the list of all subjects. This has the caveat of also
        # returning users without session data, but there currently seems
        # to be no other way to handle this.
        query = req.args.get('q', '').lower()
        db = self.env.get_db_cnx()
        cursor = db.cursor()
        cursor.execute("""SELECT DISTINCT username FROM permission""")
        usernames = [user[0] for user in self.env.get_known_users()]
        return sorted([row[0] for row in cursor if not row[0] in usernames
                       and row[0].lower().startswith(query)]) 

    def _get_users(self, req):
        # instead of known_users, could be
        # perm = PermissionSystem(self.env)
        # owners = perm.get_users_with_permission('TICKET_MODIFY')
        # owners.sort()
        # see: http://trac.edgewall.org/browser/trunk/trac/ticket/default_workflow.py#L232

        query = req.args.get('q', '').lower()

        # user names, email addresses, full names
        users = []
        for user_data in self.env.get_known_users():
            user_data = [user is not None and Chrome(self.env).format_author(req, user) or ''
                         for user in user_data]
            for index, field in enumerate((USER, EMAIL, NAME)): # ordered by how they appear
                value = user_data[field].lower()

                if value.startswith(query):
                    users.append((2-index, user_data)) # 2-index is the sort key
                    break
                if field == NAME:
                    lastnames = value.split()[1:]
                    if sum(name.startswith(query) for name in lastnames):
                        users.append((2-index, user_data)) # 2-index is the sort key
                        break

        return sorted(users)
