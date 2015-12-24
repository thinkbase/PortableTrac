# -*- coding: utf-8 -*-
#
# Copyright (c) 2007-2012 Noah Kantrowitz <noah@coderanger.net>
# All rights reserved.
#
# This software is licensed as described in the file COPYING, which
# you should have received as part of this distribution.
#

import subprocess
import re

from pkg_resources import resource_filename
from genshi.core import Markup, START, END, TEXT
from genshi.builder import tag

from trac.core import *
from trac.web.api import IRequestHandler, IRequestFilter, ITemplateStreamFilter
from trac.web.chrome import ITemplateProvider, add_stylesheet, add_script, \
                            add_ctxtnav
from trac.ticket.api import ITicketManipulator
from trac.ticket.model import Ticket
from trac.ticket.query import Query
from trac.config import Option, BoolOption, ChoiceOption
from trac.resource import ResourceNotFound
from trac.util import escape, to_unicode
from trac.util.html import html, Markup
from trac.util.text import shorten_line
from trac.util.compat import set, sorted, partial

import graphviz
from model import TicketLinks

class MasterTicketsModule(Component):
    """Provides support for ticket dependencies."""
    
    implements(IRequestHandler, IRequestFilter, ITemplateStreamFilter, 
               ITemplateProvider, ITicketManipulator)
    
    dot_path = Option('mastertickets', 'dot_path', default='dot',
                      doc='Path to the dot executable.')
    gs_path = Option('mastertickets', 'gs_path', default='gs',
                     doc='Path to the ghostscript executable.')
    use_gs = BoolOption('mastertickets', 'use_gs', default=False,
                        doc='If enabled, use ghostscript to produce nicer output.')
    
    closed_color = Option('mastertickets', 'closed_color', default='green',
        doc='Color of closed tickets')
    opened_color = Option('mastertickets', 'opened_color', default='red',
        doc='Color of opened tickets')
    show_key = Option('mastertickets', 'show_key', default=False,
        doc='Show a key for open/closed nodes')  
    closed_text = Option('mastertickets', 'closed_text', default='Done',
        doc='Text for key showing closed tickets')
    opened_text = Option('mastertickets', 'opened_text', default='ToDo',
        doc='Text for key showing opened tickets')
    highlight_target = Option('mastertickets', 'highlight_target',
        default=False, doc='Highlight target tickets in graph')
    full_graph = Option('mastertickets', 'full_graph', default=False,
        doc='Show full dep. graph, not just direct blocking links')
 
    graph_direction = ChoiceOption('mastertickets', 'graph_direction', choices = ['TD', 'LR', 'DT', 'RL'],
        doc='Direction of the dependency graph (TD = Top Down, DT = Down Top, LR = Left Right, RL = Right Left)')

    fields = set(['blocking', 'blockedby'])
    
    # IRequestFilter methods
    def pre_process_request(self, req, handler):
        return handler
        
    def post_process_request(self, req, template, data, content_type):
        if req.path_info.startswith('/ticket/'):
            # In case of an invalid ticket, the data is invalid
            if not data:
                return template, data, content_type
            tkt = data['ticket']
            links = TicketLinks(self.env, tkt)
            
            for i in links.blocked_by:
                if Ticket(self.env, i)['status'] != 'closed':
                    add_script(req, 'mastertickets/disable_resolve.js')
                    break

            # Add link to depgraph if needed
            if links:
                add_ctxtnav(req, 'Depgraph', req.href.depgraph('ticket', tkt.id))
            
            for change in data.get('changes', {}):
                if not change.has_key('fields'):
                    continue
                for field, field_data in change['fields'].iteritems():
                    if field in self.fields:
                        if field_data['new'].strip():
                            new = set([int(n) for n in field_data['new'].split(',')])
                        else:
                            new = set()
                        if field_data['old'].strip():
                            old = set([int(n) for n in field_data['old'].split(',')])
                        else:
                            old = set()
                        add = new - old
                        sub = old - new
                        elms = tag()
                        if add:
                            elms.append(
                                tag.em(u', '.join([unicode(n) for n in sorted(add)]))
                            )
                            elms.append(u' added')
                        if add and sub:
                            elms.append(u'; ')
                        if sub:
                            elms.append(
                                tag.em(u', '.join([unicode(n) for n in sorted(sub)]))
                            )
                            elms.append(u' removed')
                        field_data['rendered'] = elms
            
        #add a link to generate a dependency graph for all the tickets in the milestone
        if req.path_info.startswith('/milestone/'):
            if not data:
                return template, data, content_type
            milestone=data['milestone']
            add_ctxtnav(req, 'Depgraph', req.href.depgraph('milestone', milestone.name))


        return template, data, content_type
        
    # ITemplateStreamFilter methods
    def filter_stream(self, req, method, filename, stream, data):
        if not data:
            return stream

        # We try all at the same time to maybe catch also changed or processed templates
        if filename in ["report_view.html", "query_results.html", "ticket.html", "query.html"]:
            # For ticket.html
            if 'fields' in data and isinstance(data['fields'], list):
                for field in data['fields']:
                    for f in self.fields:
                        if field['name'] == f and data['ticket'][f]:
                            field['rendered'] = self._link_tickets(req, data['ticket'][f])
            # For query_results.html and query.html
            if 'groups' in data and isinstance(data['groups'], list):
                for group, tickets in data['groups']:
                    for ticket in tickets:
                        for f in self.fields:
                            if f in ticket:
                                ticket[f] = self._link_tickets(req, ticket[f])
            # For report_view.html
            if 'row_groups' in data and isinstance(data['row_groups'], list):
                for group, rows in data['row_groups']:
                    for row in rows:
                        if 'cell_groups' in row and isinstance(row['cell_groups'], list):
                            for cells in row['cell_groups']:
                                for cell in cells:
                                    # If the user names column in the report differently (blockedby AS "blocked by") then this will not find it
                                    if cell.get('header', {}).get('col') in self.fields:
                                        cell['value'] = self._link_tickets(req, cell['value'])
        return stream
        
    # ITicketManipulator methods
    def prepare_ticket(self, req, ticket, fields, actions):
        pass
        
    def validate_ticket(self, req, ticket):
        if req.args.get('action') == 'resolve' and req.args.get('action_resolve_resolve_resolution') == 'fixed': 
            links = TicketLinks(self.env, ticket)
            for i in links.blocked_by:
                if Ticket(self.env, i)['status'] != 'closed':
                    yield None, 'Ticket #%s is blocking this ticket'%i

    # ITemplateProvider methods
    def get_htdocs_dirs(self):
        """Return the absolute path of a directory containing additional
        static resources (such as images, style sheets, etc).
        """
        return [('mastertickets', resource_filename(__name__, 'htdocs'))]

    def get_templates_dirs(self):
        """Return the absolute path of the directory containing the provided
        ClearSilver templates.
        """
        return [resource_filename(__name__, 'templates')]

    # IRequestHandler methods
    def match_request(self, req):
        match = re.match(r'^/depgraph/(?P<realm>ticket|milestone)/(?P<id>((?!depgraph.png).)+)(/depgraph.png)?$', req.path_info)
        if match:
            req.args['realm'] = match.group('realm')
            req.args['id'] = match.group('id')
            return True

    def process_request(self, req):
        realm = req.args['realm']
        id = req.args['id']
        
        #Urls to generate the depgraph for a ticket is /depgraph/ticketnum
        #Urls to generate the depgraph for a milestone is /depgraph/milestone/milestone_name
        
        #List of tickets to generate the depgraph for
        tkt_ids=[]
        if realm == 'milestone':
            #we need to query the list of tickets in the milestone
            query = Query(self.env, constraints={'milestone': [id]}, max=0)
            tkt_ids = [fields['id'] for fields in query.execute(req)]
        else:
            #the list is a single ticket
            tkt_ids = [int(id)]

        #the summary argument defines whether we place the ticket id or
        #it's summary in the node's label
        label_summary=0
        if 'summary' in req.args:
            label_summary=int(req.args.get('summary'))

        g = self._build_graph(req, tkt_ids, label_summary=label_summary)
        if req.path_info.endswith('/depgraph.png') or 'format' in req.args:
            format = req.args.get('format')
            if format == 'text':
                #in case g.__str__ returns unicode, we need to convert it in ascii
                req.send(to_unicode(g).encode('ascii', 'replace'), 'text/plain')
            elif format == 'debug':
                import pprint
                req.send(
                    pprint.pformat(
                        [TicketLinks(self.env, tkt_id) for tkt_id in tkt_ids]
                        ),
                    'text/plain')
            elif format is not None:
                req.send(g.render(self.dot_path, format), 'text/plain')
            
            if self.use_gs:
                ps = g.render(self.dot_path, 'ps2')
                gs = subprocess.Popen([self.gs_path, '-q', '-dTextAlphaBits=4', '-dGraphicsAlphaBits=4', '-sDEVICE=png16m', '-sOutputFile=%stdout%', '-'], 
                                      stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
                img, err = gs.communicate(ps)
                if err:
                    self.log.debug('MasterTickets: Error from gs: %s', err)
            else:
                img = g.render(self.dot_path)
            req.send(img, 'image/png')
        else:
            data = {}
            
            #add a context link to enable/disable labels in nodes
            if label_summary:
                add_ctxtnav(req, 'Without labels', req.href(req.path_info, summary=0))
            else:
                add_ctxtnav(req, 'With labels', req.href(req.path_info, summary=1))

            if realm == 'milestone':
                add_ctxtnav(req, 'Back to Milestone: %s' % id, req.href.milestone(id))
                data['milestone'] = id
            else:
                data['ticket'] = id
                add_ctxtnav(req, 'Back to Ticket #%s' % id, req.href.ticket(id))
            data['graph'] = g
            data['graph_render'] = partial(g.render, self.dot_path)
            data['use_gs'] = self.use_gs
            
            return 'depgraph.html', data, None

    def _build_graph(self, req, tkt_ids, label_summary=0):
        g = graphviz.Graph()
        g.label_summary = label_summary

        g.attributes['rankdir'] = self.graph_direction
        
        node_default = g['node']
        node_default['style'] = 'filled'
        
        edge_default = g['edge']
        edge_default['style'] = ''
        
        # Force this to the top of the graph
        for id in tkt_ids:
            g[id] 

        if self.show_key:
            g[-1]['label'] = self.closed_text
            g[-1]['fillcolor'] = self.closed_color
            g[-1]['shape'] = 'box'
            g[-2]['label'] = self.opened_text
            g[-2]['fillcolor'] = self.opened_color
            g[-2]['shape'] = 'box'

        links = TicketLinks.walk_tickets(self.env, tkt_ids,
            full=self.full_graph)
        links = sorted(links, key=lambda link: link.tkt.id)
        for link in links:
            tkt = link.tkt
            node = g[tkt.id]
            if label_summary:
                node['label'] = u'#%s %s' % (tkt.id, tkt['summary'])
            else:
                node['label'] = u'#%s'%tkt.id
            node['fillcolor'] = tkt['status'] == 'closed' and self.closed_color or self.opened_color
            node['URL'] = req.href.ticket(tkt.id)
            node['alt'] = u'Ticket #%s'%tkt.id
            node['tooltip'] = escape(tkt['summary'])
            if self.highlight_target and tkt.id in tkt_ids:
                node['penwidth'] = 3
            
            for n in link.blocking:
                node > g[n]
        
        return g

    def _link_tickets(self, req, tickets):
        items = []

        for i, word in enumerate(re.split(r'([;,\s]+)', tickets)):
            if i % 2:
                items.append(word)
            elif word:
                ticketid = word
                word = '#%s' % word

                try:
                    ticket = Ticket(self.env, ticketid)
                    if 'TICKET_VIEW' in req.perm(ticket.resource):
                        word = \
                            tag.a(
                                '#%s' % ticket.id,
                                class_=ticket['status'],
                                href=req.href.ticket(int(ticket.id)),
                                title=shorten_line(ticket['summary'])
                            )
                except ResourceNotFound:
                    pass
               
                items.append(word)

        if items:
            return tag(items)
        else:
            return None
