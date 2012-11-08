# -*- coding: utf-8 -*-

from genshi.builder import tag

from trac.core import *
from trac.resource import *
from trac.ticket.query import *

from pptickets import *


class BaseFilter():
  '''
    Filter Superclass for Basic Filters
  '''

  # dont retrive the description, this is pure bloat
  IGNORE_FIELDS= [] # e.g. [ u'description' ]

  def __init__( self, macroenv ):
    '''
      Initialize the Base Filter with Columns for Data retrival.
    '''
    self.macroenv = macroenv
    self.ticketset = {}
    self.cols = [ f['name'] for f in TicketSystem( self.macroenv.tracenv ).get_ticket_fields() ];
    for i in self.IGNORE_FIELDS:
      if i in self.cols:
        self.cols.remove( i )
    # transform ['col1','col2',...] list into "col=col1&col=col2&.." string
    self.colsstr = reduce( lambda x, y: x+'&'+y, map( lambda x: "col="+x, self.cols ) )
    # max_ticket_number_at_filters can be attached to trac.ini
    try:
      self.max_ticket_number_at_filters = self.macroenv.conf.get('max_ticket_number_at_filters')
    except Exception,e:
      self.macroenv.tracenv.log.warning('init max_ticket_number_at_filters (fallback): '+repr(e))
      self.max_ticket_number_at_filters = '1000' # fallback, Trac default was 100

  def get_tickets( self ):
    '''
      Return a TicketSet.
      In this case it is Empty, since BaseFilter does Nothing.
    '''
    return self.ticketset

  def get_ticket_ids( self ):
    '''
      Return a List of Ticket Ids
      In this case it is Empty, since BaseFilter does Nothing.
    '''
    ticket_ids = []
    for t in self.get_tickets():
      ticket_ids.append(t['id'])
    return ticket_ids

class ParamFilter( BaseFilter ):
  '''
    Base Class for Filters that require a Parameter.
  '''
  def __init__( self, macroenv ):
    '''
      Initialize the Base Filter
    '''
    BaseFilter.__init__( self, macroenv )
    self.queryarg = ""

  def set_queryarg( self, q ):
    '''
      Set the Parameter.
    '''
    self.queryarg = q

class NullFilter( BaseFilter ):
  '''
    Filter for "No Filtering", simply returns everything
  '''
  def get_tickets( self ):
    '''
      Return all Tickets using trac.ticket.query.Query
    '''
    
    return Query( self.macroenv.tracenv, order='id', cols=self.cols, max=self.max_ticket_number_at_filters ).execute( self.macroenv.tracreq )

class QueryFilter( ParamFilter ):
  '''
    Class for Query Based Filters
  '''

  def __init__( self, macroenv ):
    '''
      Initialize the Base Filter
    '''
    ParamFilter.__init__( self, macroenv )
    self.filtercol = ""
    self.operator = '=' # equal-filter
    self.filterlist = {}
    self.filterlistcustom = {}

  def set_col( self, c ):
    '''
      Set the Column for the Query.
      (The Query/Filter Parameter is passed to ParamFilter.set_queryarg)
    '''
    if self.filtercol in self.cols:
      self.cols.remove( self.filtercol )
    self.filtercol = c
  
  def set_queryoperator_not( self ):
    self.operator = '!='

  def set_queryoperator_like( self ):
    self.operator = '=~'

  def add_query_col_and_arg(self, col, operator, arg):
    '''
      easy access to create AND query with several arguments
    '''
    self.filterlist[col] = (operator, arg)

  def add_query_customcol_and_arg(self, col, operator, arg):
    '''
      easy access to create AND query with several arguments of a custom ticket value
    '''
    self.filterlistcustom[col] = (operator, arg)

  def get_tickets_custom( self ):
    '''
      Query the Database including ticket_custom and return result set
    '''
    
    def translate2sqlcommands( colname, filtertupel ):
      values = filtertupel[1].split('|') # splits the list of values like TracQuery
      sqlmore = [] # list of sql where clauses
      
      if filtertupel[0] == '!=':
        glue = ' AND '
      else:
        glue = ' OR '
      
      for value in values:
        if filtertupel[0] == '=~':
          sep = '%'
          sqlmore.append('%s LIKE "%s%s%s"' % (colname, sep, value, sep))
        else:
          sqlmore.append(colname+' '+filtertupel[0]+' "'+value+'" ')
      return '(%s)' % ( glue.join(sqlmore)  ) # create a summarized SQL where clause
    
    
    wherefilter = []
    for filtercol in self.filterlist.keys():
      wherefilter.append( ' %s ' % (translate2sqlcommands(filtercol, self.filterlist[filtercol]) ) )
    
    self.macroenv.tracenv.log.debug('self.filterlistcustom: '+repr(self.filterlistcustom) )
    for filtercustomcol in self.filterlistcustom.keys():
      wherefilter.append( ' id IN ( SELECT ticket FROM ticket_custom WHERE name="%s" AND %s ) ' % (filtercustomcol, translate2sqlcommands('value', self.filterlistcustom[filtercustomcol]) ) )
    
    wherefilter = '  AND '.join(wherefilter)
    wherefilter = ' SELECT id FROM ticket WHERE '+wherefilter
    self.macroenv.tracenv.log.debug("translate2sqlcommands sql: "+wherefilter);
    
    db = self.macroenv.tracenv.get_db_cnx() 
    cursor = db.cursor()
    cursor.execute(wherefilter)
    ticket_ids = cursor.fetchall()
    
    # query for all these tickets
    querystr = '0'
    for ticket_id in ticket_ids:
      querystr = '%s|%s' % (ticket_id[0], querystr )
    querystr = 'id=%s' % (querystr)
    querystr = '%s&%s' % ( querystr, self.colsstr ) # choose columns 
    
    
    #self.macroenv.tracenv.log.warning('get_tickets_list: '+querystr )
    q = Query.from_string(self.macroenv.tracenv, querystr, max=self.max_ticket_number_at_filters , order='id' )
    return q.execute( self.macroenv.tracreq )

  def get_tickets( self ):
    '''
      Query the Database and return
    '''
    if self.filterlist != {}: # several attributes are given
      querystr = ''
      for filtercol in self.filterlist.keys():
        querystr = '%s%s%s&%s' % (filtercol, self.filterlist[filtercol][0], self.filterlist[filtercol][1], querystr )
      querystr = '%s%s' % ( querystr, self.colsstr )
      self.macroenv.tracenv.log.warning('QueryFilterSum: '+querystr )
      q = Query.from_string(self.macroenv.tracenv, querystr, max=self.max_ticket_number_at_filters , order='id' )
      return q.execute( self.macroenv.tracreq )
      
    elif self.filtercol: # only one col is given as filter
      #self.macroenv.tracenv.log.debug('QueryFilter: %s%s%s&%s' % ( self.filtercol, self.operator, self.queryarg, self.colsstr ) )
      q = Query.from_string(self.macroenv.tracenv, '%s%s%s&%s' % ( self.filtercol, self.operator, self.queryarg, self.colsstr ), max=self.max_ticket_number_at_filters , order='id' )
      return q.execute( self.macroenv.tracreq )
      
    else: # nothing given select all tickets
      return NullFilter( self.macroenv ).get_tickets()

class AuthedOwnerFilter( QueryFilter ):
  '''
    Special Query Filter Class, which returns the Tickets for the currently
    authenticated Owner
  '''

  def __init__( self, macroenv ):
    '''
      Initialize and set QueryFilter args
    '''
    QueryFilter.__init__( self, macroenv )
    self.set_col( 'owner' )
    self.set_queryarg( self.macroenv.tracreq.authname )

class AuthedReporterFilter( QueryFilter ):
  '''
    Special Query Filter Class, which returns the Tickets for the currently
    authenticated Reporter
  '''

  def __init__( self, macroenv ):
    '''
      Initialize and set QueryFilter args
    '''
    QueryFilter.__init__( self, macroenv )
    self.set_col( 'reporter' )
    self.set_queryarg( self.macroenv.tracreq.authname )

class TicketBiDepGraphFilter( ParamFilter ):
  '''
    Special Query Filter Class, which returns the Tickets depending on
    self.queryarg (ticket id)
  '''
  cache = None

  DEPEXTENSION = ''

  def __init__( self, macroenv ):
    '''
      Initialize the Base Filter
    '''
    ParamFilter.__init__( self, macroenv )

  def get_tickets( self ):
    '''
      Query Database and Calculate Dependencies
    '''
    # get param
    v = self.queryarg
    self.macroenv.tracenv.log.debug('TicketBiDepGraphFilter: BEGIN %s  %s' % (self.DEPEXTENSION, v))
    # cached result values
    if self.cache != None:
      return self.cache 
    
    # query data
    ticketset = ppTicketSet( self.macroenv )
    ticketdata = NullFilter( self.macroenv ).get_tickets()
    for t in ticketdata:
      ticketset.addTicket(t)
    
    # calculate deps
    depqueue = list()
    depset = set()
    depqueue.append( int( v ) )
    depset.add( int( v ) )
    ticketset.needExtension( self.DEPEXTENSION )
    while len( depqueue ) > 0:
      #self.macroenv.tracenv.log.debug('TicketBiDepGraphFilter: depqueue: %s ' % (repr(depqueue)))
      current = depqueue.pop( 0 )
      cdata = ticketset.getTicket( current )
      deps = cdata.getextension( self.DEPEXTENSION )
      for d in deps:
        if int( d.getfield( 'id' ) ) not in depset:
          depqueue.append( int( d.getfield( 'id' ) ) )
          depset.add( int( d.getfield( 'id' ) ) )
    
    # build ticketlist with deps
    del ticketset
    depdata = list()
    for t in ticketdata:
      if int( t[ 'id' ] ) in depset:
         depdata.append( t )
    del ticketdata
    for t in depdata:
      self.macroenv.tracenv.log.debug('TicketBiDepGraphFilter: Result: %s' % (repr(t['id'])))
    
    self.cache = depdata # save calculated values
    return depdata

class TicketDepGraphFilter( TicketBiDepGraphFilter ):
  DEPEXTENSION = 'dependencies'


class TicketRevDepGraphFilter( TicketBiDepGraphFilter ):
  DEPEXTENSION = 'reverse_dependencies'


class ppFilter():
  '''
    Filter Director.
    Basic Class for usage of BaseFilter Filter. It checks for several
    Arguments and KW pairs in the given KW dict and Args List and Returns
    a ppTicketSet using the specified Filters.
  '''
  OPERATOR_AND = 'AND'
  OPERATOR_OR = 'OR'
  
  def __init__(self, macroenv):
    '''
      Initialize
    '''
    self.macroenv = macroenv

  def get_tickets(self):
    '''
      Build a ppTicketSet with Filters, specified in the Args List and
      KW Dict. On "notickets" Argument this will return an empty ppTicketSet,
      while no given Arguments and KW Paris will result in a complete ppTicketSet.
      This behavior and Filter execution can be change in this method.
    '''
    # skip queries, when 'notickets' arg is passed
    ticketset = ppTicketSet( self.macroenv )
    if 'notickets' in self.macroenv.macroargs:
      return ticketset

    filtered = False
    # entries: <kw key>: <query column>
    query_filters = {
      'filter_milestone': 'milestone',
      'filter_component': 'component',
      'filter_id':'id',
      'filter_type':'type',
      'filter_severity':'severity',
      'filter_priority':'priority',
      'filter_owner':'owner',
      'filter_reporter':'reporter',
      'filter_cc':'cc',
      'filter_version':'version',
      'filter_status':'status',
      'filter_resolution':'resolution',
      'filter_keywords':'keywords'
    }
    
    # every inverted filter
    query_notfilters = {
      'filternot_milestone': 'milestone',
      'filternot_component': 'component',
      'filternot_id':'id',
      'filternot_type':'type',
      'filternot_severity':'severity',
      'filternot_priority':'priority',
      'filternot_owner':'owner',
      'filternot_reporter':'reporter',
      'filternot_cc':'cc',
      'filternot_version':'version',
      'filternot_status':'status',
      'filternot_resolution':'resolution',
      'filternot_keywords':'keywords'
    }
    
    # every inverted filter
    query_likefilters = {
      'filterlike_milestone': 'milestone',
      'filterlike_component': 'component',
      'filterlike_id':'id',
      'filterlike_type':'type',
      'filterlike_severity':'severity',
      'filterlike_priority':'priority',
      'filterlike_owner':'owner',
      'filterlike_reporter':'reporter',
      'filterlike_cc':'cc',
      'filterlike_version':'version',
      'filterlike_status':'status',
      'filterlike_resolution':'resolution',
      'filterlike_keywords':'keywords'
    }

    # entries: <kw key>: <ParamFilter cls>
    # - value is passed with cls.set_queryarg, afterwards cls.get_tickets() is called
    param_filters = {
      'filter_ticketdeps': TicketDepGraphFilter,
      'filter_ticketrdeps': TicketRevDepGraphFilter
    }

    # entries: <args key>: <BaseFilter cls>
    # - only get_tickets() is called
    nullparam_filters = {
      'filter_owned': AuthedOwnerFilter,
      'filter_reported': AuthedReporterFilter
    }
    
    operator = self.macroenv.macrokw.get('combine_filters')
    
    # translate the keyword to a unified operator
    if operator != None:
      if operator.upper() in [ 'AND' , 'INTERSECT' ]:
        operator = self.OPERATOR_AND
      elif operator.upper() in [ 'OR' , 'UNION' ]:
        operator = self.OPERATOR_OR
      else:
        operator = None
    else: 
      # Fallback
      operator = self.OPERATOR_OR
    
    self.macroenv.tracenv.log.debug('combine_filters:'+str(operator))
    
    # intersect all tickets initially if operator is AND
    if operator == self.OPERATOR_AND:
      
      def check_filter_on_ticket_custom_field( k, v, filtertype, filteroperator ):
        '''
          register user filter for a field out of ticket-custom
          precondition: the field actally exists within the ticket-custom section in trac.ini
        '''
        self.macroenv.tracenv.log.debug(filtertype+' found: '+k+'='+v)
        ticket_custom_field = k[len(filtertype):]
        if self.macroenv.conf.get_ticket_custom(ticket_custom_field) :
          f.add_query_customcol_and_arg( ticket_custom_field , filteroperator, v )
        else:
          # this might happen for example while using "filter_ticketdeps"
          self.macroenv.tracenv.log.warning(filtertype+' NOT found in conf: '+k+'='+v+'  --> '+repr(self.macroenv.conf.get_ticket_custom(ticket_custom_field)))
      
      # combine all and filter in one query
      f = QueryFilter( self.macroenv )
      for ( k, v ) in self.macroenv.macrokw.items():
        if k in query_filters:
          f.add_query_col_and_arg( query_filters[k] , '=', v )
        elif k in query_notfilters:
          f.add_query_col_and_arg( query_notfilters[k] , '!=', v )
        elif k in query_likefilters:
          f.add_query_col_and_arg( query_likefilters[k] , '=~', v )
        elif k.startswith('filter_'):  # custom field filter
          check_filter_on_ticket_custom_field( k, v, 'filter_', '=' )
        elif k.startswith('filternot_'): # custom field filter
          check_filter_on_ticket_custom_field( k, v, 'filternot_', '!=' )
        elif k.startswith('filterlike_'): # custom field filter
          check_filter_on_ticket_custom_field( k, v, 'filterlike_', '=~' )
        else: 
          self.macroenv.tracenv.log.debug(k+' is not a filter: '+k+'='+v)
      
      # add tickets 
      for t in f.get_tickets_custom():
        #self.macroenv.tracenv.log.error('ticket:'+repr((t)))
        ticketset.addTicket( t )
    #else:
      #ticketlist = NullFilter( self.macroenv ).get_tickets() # OR
    #self.macroenv.tracenv.log.error('pre-ticketset:'+repr(dir(ticketlist)))
    #self.macroenv.tracenv.log.error('pre-ticketset:'+repr(ticketlist))
    
    
    #ticketset = ppTicketSet() # OR
    # get tickets for "Parameter based Filters" using macrokw
    # TODO: need to refactor, duplicate code; need to speed up OR-filter-operator
    global_filtered = False # was there every a filter applied
    for ( k, v ) in self.macroenv.macrokw.items():
      filtered = False
      #self.macroenv.tracenv.log.warning('filter: '+repr(k))
      
      # do not perform each single query at AND, because it is not performant
      if k in query_filters and operator != self.OPERATOR_AND:
        # get list of tickets
        #self.macroenv.tracenv.log.debug('query_filters:'+repr(k)+' '+repr(query_filters[ k ])+' '+repr(v) )
        f = QueryFilter( self.macroenv )
        f.set_col( query_filters[ k ] )
        f.set_queryarg( v )
        filtered = True
        
      # do not perform each single query at AND, because it is not performant
      elif k in query_notfilters and operator != self.OPERATOR_AND:
        # get list of tickets
        #self.macroenv.tracenv.log.debug('query_notfilters:'+repr(k)+' '+repr(query_notfilters[ k ])+' '+repr(v) )
        f = QueryFilter( self.macroenv )
        f.set_col( query_notfilters[ k ] )
        f.set_queryarg( v )
        f.set_queryoperator_not( )
        filtered = True
        
      # do not perform each single query at AND, because it is not performant
      elif k in query_likefilters and operator != self.OPERATOR_AND:
        # get list of tickets
        #self.macroenv.tracenv.log.debug('query_notfilters:'+repr(k)+' '+repr(query_notfilters[ k ])+' '+repr(v) )
        f = QueryFilter( self.macroenv )
        f.set_col( query_likefilters[ k ] )
        f.set_queryarg( v )
        f.set_queryoperator_like( )
        filtered = True
        
      elif k in param_filters:
        #self.macroenv.tracenv.log.debug('param_filters:'+repr(k))
        f = param_filters[ k ]( self.macroenv )
        f.set_queryarg( v )
        filtered = True
      
      #self.macroenv.tracenv.log.warning('filter: 010 ('+str(len(ticketset.getIDList()))+'):'+repr(ticketset.getIDList()))
      if filtered:
        global_filtered = True
        #self.macroenv.tracenv.log.warning('currentTickets: '+repr(ticketset.getIDList()))
        # adapt ticket set
        if operator == self.OPERATOR_AND:
          #self.macroenv.tracenv.log.debug('intersect allowedTickets: '+repr(f.get_tickets()))
          for tid in ticketset.getIDList():
            if not tid in f.get_ticket_ids(): # allowedTicketIDs
              ticketset.deleteTicketId( tid )
              #self.macroenv.tracenv.log.debug('remove ticket: '+str(tid))
        elif operator == self.OPERATOR_OR: # OR
          #self.macroenv.tracenv.log.debug('union allowedTickets: '+repr(f.get_tickets()))
          for t in f.get_tickets():
            ticketset.addTicket( t )
        else:
          raise Exception('Unknown Filter Operator: '+repr(operator)+' ('+repr(self.macroenv.macrokw.get('combine_filters'))+')')
    
    # Fallback, so no filter means all tickets
    if global_filtered == False and operator == self.OPERATOR_OR:
      ticketlist = NullFilter( self.macroenv ).get_tickets() #  all tickets
      for t in ticketlist:
        ticketset.addTicket(t)
    
    #self.macroenv.tracenv.log.debug('filter: result ids: ticketset ('+str(len(ticketset.getIDList()))+'):'+repr(ticketset.getIDList()))
    return ticketset



class ppFilterOld():
  '''
    Filter Director.
    Basic Class for usage of BaseFilter Filter. It checks for several
    Arguments and KW pairs in the given KW dict and Args List and Returns
    a ppTicketSet using the specified Filters.
  '''
  def __init__(self, macroenv):
    '''
      Initialize
    '''
    self.macroenv = macroenv

  def get_tickets(self):
    '''
      Build a ppTicketSet with Filters, specified in the Args List and
      KW Dict. On "notickets" Argument this will return an empty ppTicketSet,
      while no given Arguments and KW Paris will result in a complete ppTicketSet.
      This behavior and Filter execution can be change in this method.
    '''
    # skip queries, when 'notickets' arg is passed
    ticketset = ppTicketSet( self.macroenv )
    if 'notickets' in self.macroenv.macroargs:
      return ticketset

    filtered = False
    # entries: <kw key>: <query column>
    query_filters = {
      'filter_milestone': 'milestone',
      'filter_component': 'component',
      'filter_id':'id',
      'filter_type':'type',
      'filter_severity':'severity',
      'filter_priority':'priority',
      'filter_owner':'owner',
      'filter_reporter':'reporter',
      'filter_version':'version',
      'filter_status':'status',
      'filter_resolution':'resolution',
      'filter_keywords':'keywords'
    }

    # entries: <kw key>: <ParamFilter cls>
    # - value is passed with cls.set_queryarg, afterwards cls.get_tickets() is called
    param_filters = {
      'filter_ticketdeps': TicketDepGraphFilter,
      'filter_ticketrdeps': TicketRevDepGraphFilter
    }

    # entries: <args key>: <BaseFilter cls>
    # - only get_tickets() is called
    nullparam_filters = {
      'filter_owned': AuthedOwnerFilter,
      'filter_reported': AuthedReporterFilter
    }

    # get tickets for "Parameter based Filters" using macrokw
    for ( k, v ) in self.macroenv.macrokw.items():
      parmfilter = False
      self.macroenv.tracenv.log.error('Filter:'+repr(k))
      if k in query_filters:
        f = QueryFilter( self.macroenv )
        f.set_col( query_filters[ k ] )
        f.set_queryarg( v )
        parmfilter = True
      elif k in param_filters:
        f = param_filters[ k ]( self.macroenv )
        f.set_queryarg( v )
        parmfilter = True
      if parmfilter:
        ticketlist = f.get_tickets()
        # merge (OR like)
        for t in ticketlist:
          ticketset.addTicket( t )
        del ticketlist
        filtered = True

    # get tickets for "Null Parameter based Filters" using macroargs
    for k in self.macroenv.macroargs:
      if k in nullparam_filters:
        f = nullparam_filters[ k ]( self.macroenv )
        ticketlist = f.get_tickets()
        # merge
        for t in ticketlist:
          ticketset.addTicket( t )
        del ticketlist
        filtered = True

    # fallback to NullFilter, when nothin done
    if not filtered:
      ticketlist = NullFilter( self.macroenv ).get_tickets()
      for t in ticketlist:
        ticketset.addTicket(t)
      del ticketlist

    return ticketset
