# -*- coding: utf-8 -*-

import datetime
import pputil
from trac.util.datefmt import to_datetime, utc
from trac.ticket.model import Ticket

class TSExtensionRegister(object):
  '''
    TicketSet Extension Register
  '''
  # TODO: Class for Render/TicketSet Extension, with Documentation such that
  # Documentation can be generated for the Macro (Trac WikiMacro Listing)
  __r = {}

  @classmethod
  def add(cls,registrantcls,registername):
    '''
      Add a TSExtension:Name pair into the Register
    '''
    cls.__r[ registername ] = registrantcls

  @classmethod
  def keys(cls):
    '''
      Enumerate the Names
    '''
    return cls.__r.keys()

  @classmethod
  def get(cls,registername):
    '''
      Get the Matching Extension for a given Name
    '''
    return cls.__r[ registername ]

class ppTicket():
  '''
    Project Plan Ticket Class for extended Ticket Attributes
  '''
  def __init__(self,dataref,ticketset):
    '''
      initialize ticket object with data reference (dict with stored ticket data) and
      ticketset (ppTicketSet object which holds this object)
    '''
    self.__dataref = dataref
    self.__extensions = dict()

  def hasfield(self,name):
    '''
      check wether ticketdata has a key <name>
    '''
    return name in self.__dataref

  def getfield(self,name):
    '''
      return ticketdata for key <name>
    '''
    return self.__dataref[ name ]

  def getfielddefs( self ):
    '''
      return the set of valid fields
    '''
    #return self.__dataref.keys()
    return TicketSet.getfielddefs()

  def getfielddef(self,name,defval):
    '''
      return ticketdata for key <name> or default if theres no data
    '''
    if self.hasfield(name) and self.getfield(name):
      return self.__dataref[ name ]
    else:
      return defval

  def hasextension(self,name):
    '''
      check wether ticket extension with key <name> exists
    '''
    return name in self.__extensions

  def getextension(self,name):
    '''
      return ticket extension for key <name> or None
    '''
    if self.hasextension( name ):
      return self.__extensions[ name ]
    else:
      return None

  def _setextension(self,name,data):
    '''
      set an extension field
    '''
    self.__extensions[ name ] = data

  def _delextension(self,name):
    '''
      delete an extension field (which is f.e. temporary used for an extension)
    '''
    del self.__extensions[ name ]

  def get_changelog( self ):
    t = Ticket(self.env, id)
    return( t.get_changelog() )
  
  def getstatus( self ):
    '''
      return status of ticket
    '''
    return self.getfield('status')
  
  def getpriority( self ) :
    '''
      return priority of ticket
    '''
    return self.getfield('priority')
 

class ppTicketSet():

  def __init__(self, macroenv):
    '''
      Initialize the ppTicketSet
    '''
    self.__extensions = dict()
    self.macroenv = macroenv
    self.__tickets = dict()

  def addTicket(self,ticket):
    '''
      add a new ticket with ticket data <ticket>
    '''
    #self.macroenv.tracenv.log.debug('addTicket: '+repr(ticket) )
    self.__tickets[ ticket['id'] ] = ppTicket(ticket,self)

  def deleteTicket(self,ticket):
    '''
      remove a new ticket with ticket data <ticket>
    '''
    self.deleteTicketId(ticket['id'])

  def deleteTicketId(self, tid):
    try:
      del self.__tickets[ tid ]
    except:
      pass

  @classmethod
  def getfielddefs( self ):
    return [ f['name'] for f in TicketSystem( self.macroenv.tracenv ).get_ticket_fields() ]

  def getIDList(self):
    '''
      return a list of ticket ids of tickets in this set
    '''
    return self.__tickets.keys();

  def getIDSortedList(self):
    '''
      return a  sorted list of ticket ids of tickets in this set
    '''
    idlist = self.__tickets.keys();
    idlist.sort()
    return idlist

  def getTicket(self,id):
    '''
      return the ppTicket object for a ticket with id <id>
    '''
    try:
      return self.__tickets[ id ]
    except KeyError:
      raise Exception('ticket not available: #%s (maybe increase the value of max_ticket_number_at_filters)' % (id,))

  def hasExtension(self,name):
    '''
      check wether ticketset extension with key <name> exists
    '''
    return name in self.__extensions

  def getExtension(self,name):
    '''
      return ticketset extension for key <name> or None
    '''
    if self.hasExtension( name ):
      return self.__extensions[ name ]
    else:
      return None

  def needExtension(self,name):
    '''
      execute an extension on this ticketset
    '''
    if self.hasExtension( name ):
      return
    else:
      if name in TSExtensionRegister.keys():
        extcls = TSExtensionRegister.get( name )
        if (extcls!=None):
          extensiono = extcls( self, self.__tickets )
          if (extensiono!=None):
            exttsdata = extensiono.extend()
            self.__extensions[ name ] = exttsdata
            return
      raise TracError( 'extension "%s" went missing or failed' % name )

  def get_changelog( self , ticketid):
    t = Ticket(self.macroenv.tracenv, ticketid)
    try: 
      return( t.get_changelog() )
    except:
      self.macroenv.tracenv.log.warn("get_changelog failed on ticket %s", ticketid)
      return [] # no changelogs


class ppTicketSetExtension():
  '''
    Base Class for TicketSet Extensions
  '''

  def __init__(self,ticketset,ticketsetdata):
    pass

  def extend(self):
    '''
      Execute the Extension and Extend Tickets and/or TicketSet with
      Extension fields. Return anything except None to Mark this extension
      as Executed. The Value will be put in the matching extension field for
      this Extension.
    '''
    return True

TSExtensionRegister.add( ppTicketSetExtension, 'base' )

class ppTSLastChange( ppTicketSetExtension ):
  '''
    Get the Last Ticket Changetime
  '''

  def __init__(self,ticketset,ticketsetdata):
    self.__ts = ticketsetdata

  def extend(self):
    '''
      Check for all Changetimes and Return the highest Changetime as
      Int
    '''
    timemax = to_datetime( 0, utc )
    timenow = to_datetime( datetime.datetime.now(utc) )
    for k in self.__ts:
      v = self.__ts[ k ]
      ticketdt = to_datetime( v.getfielddef( 'changetime', timenow ) )
      if ticketdt > timemax:
        timemax = ticketdt
        if timemax == timenow:
          break
    return timemax

TSExtensionRegister.add( ppTSLastChange, 'tslastchange' )

class ppTSSetOfField( ppTicketSetExtension ):
  '''
    Generate a Set (List of non-duplicate Values), for
    a given Field.
  '''

  FieldName = ''
  DefValue = ''

  def __init__(self,ticketset,ticketsetdata):
    '''
      Get the Ticketdata
    '''
    self.__ts = ticketsetdata

  def extend(self):
    '''
      Put all Values into a Set and Sort it.
      Return the Sorted Set for values of the given field.
    '''
    vset = set()
    for k in self.__ts:
      vset.add( self.__ts[ k ].getfielddef( self.FieldName, self.DefValue ) )
    return sorted( vset )

class ppTSVersions( ppTSSetOfField ):
  '''
    Generate a Sorted Set for the Version field
  '''

  FieldName = 'version'

TSExtensionRegister.add( ppTSVersions, 'tsversions' )

class ppTSMilestones( ppTSSetOfField ):
  '''
  Generate a Sorted Set for the Milestone field
  '''

  FieldName = 'milestone'

TSExtensionRegister.add( ppTSMilestones, 'tsmilestones' )

class ppTSDependencies( ppTicketSetExtension ):
  '''
    Generate a Dependency List which holds ppTicket Instances for the
    current TicketSet and another List which holds IDs for those
    Dependencies, which cant be resolved. (either because the
    there is no Instance for this Ticket in the current TicketSet or the
    Ticket with the given ID does not exist)
  '''

  def __init__(self,ticketset,ticketsetdata):
    self.__tso = ticketset
    self.__ts = ticketsetdata

  def extend(self):
    '''
      Calculate the field dependencies, which holds ppTicket Instances
      and the field all_dependencies which holds all given Ticket IDs, written
      in the dependency field for the current Ticket.
    '''
    depfield = self.__tso.macroenv.conf.get( 'custom_dependency_field' )

    for k in self.__ts:
      v = self.__ts[ k ]
      intset = pputil.ticketIDsFromString( v.getfielddef( depfield, '' ) )
      v._setextension( 'all_dependencies', intset )
      depset = set()
      for d in intset:
        if d in self.__ts:
          depset.add( self.__ts[ d ] )
      v._setextension( 'dependencies', depset )
    return True

TSExtensionRegister.add( ppTSDependencies, 'dependencies' )

class ppTSReverseDependencies( ppTicketSetExtension ):
  '''
    Calculate the reverse Dependencies for the dependencies extension field.
    This is a list of ppTicket Instances. The reverse dependencies field
    is also depending on the given TicketSet. Tickets not in this set, cant be
    set as reverse dependencies!
  '''

  def __init__(self,ticketset,ticketsetdata):
    self.__ts = ticketsetdata
    ticketset.needExtension( 'dependencies' )

  def extend(self):
    '''
      calculate the reverse_dependencies field based on the dependencies field.
    '''
    for k in self.__ts:
      self.__ts[ k ]._setextension( 'reverse_dependencies', set() )
    # reverse dependency calculation
    for k in self.__ts:
      v = self.__ts[ k ]
      for d in v.getextension( 'dependencies' ):
        d.getextension( 'reverse_dependencies' ).add( v )
    return True

TSExtensionRegister.add( ppTSReverseDependencies, 'reverse_dependencies' )

class ppTSDueTimes( ppTicketSetExtension ):
  '''
    Calculate the time values.
    First, convert the given Text for Assign/Close Time into DateTime Values.
    Second, calculate Worktime / Assigndelay / Closingdelay without
    accessing the Database.
    Third, calculate Start and Finish Dates.
  '''

  def __init__(self,ticketset,ticketsetdata):
    '''
      Initialize with ticketset, ticketdata and calculate dependencies
    '''
    self.__tso = ticketset
    self.__ts = ticketsetdata
    if not ticketset.needExtension( 'dependencies' ):
      self = None

  def fieldtodatetime(self,v,field,dtf):
    '''
      convert a field, with given day/month/year mask into
      a datetime value
    '''
    theDate = v.getfielddef( field, 'DD/MM/YYYY' )
    if theDate != '' and theDate != 'MM/DD/YYYY' and theDate != 'DD/MM/YYYY':
      AtheDate = None
      if dtf == 'DD/MM/YYYY':
        AtheDate = theDate.split('/');
        day_key = 0;
        month_key = 1;
        year_key = 2;
      if dtf == 'MM/DD/YYYY':
        AtheDate = theDate.split('/');
        month_key = 0;
        day_key = 1;
        year_key = 2;
      if dtf == 'DD.MM.YYYY':
        AtheDate = theDate.split('.');
        day_key = 0;
        month_key = 1;
        year_key = 2;
      if dtf == 'YYYY-MM-DD':
        AtheDate = theDate.split('-');
        year_key = 0;
        month_key = 1;
        day_key = 2;

      try:
        if AtheDate and len(AtheDate) == 3:
          year=int(AtheDate[year_key]);
          month=int(AtheDate[month_key]);
          day=int(AtheDate[day_key]);
          #return datetime.datetime(year,month,day)
          return datetime.date(year,month,day) # catch 64 bit problem
      except:
        # a problem appears, while parsing the date field
        # TODO: raise error message
        pass

    return None

  def extend(self):
    '''
      Calculate Datetime Values for Assign and Closing Time,
      calculate the difference to the current time in days and attach
      them into assigndiff and closingdiff extension fields for each ticket.
      Calculate the Workload (closing-assigntime) or set a Defaultworkload.
      Calculate start and finish Dates for each ticket, where both are
      either depending on the assign and closing time when it is on time or
      calculate start/finish date from now, such that workload is always the same,
      but start and finish are moving on overdue.

      no time is calculated, when both assign and close time are not given.
      (there is no dependency usage in the time calculation)
    '''
    adatefield = self.__tso.macroenv.conf.get( 'custom_due_assign_field' )
    cdatefield = self.__tso.macroenv.conf.get( 'custom_due_close_field' )
    adateformat = self.__tso.macroenv.conf.get( 'ticketassignedf' )
    cdateformat = self.__tso.macroenv.conf.get( 'ticketclosedf' )
    #dateNow = datetime.datetime.today()
    dateNow = datetime.date.today() # catch 64 bit problems

    for k in self.__ts:
      v = self.__ts[ k ]
      # set datetime values for assign/close - those can be None!
      adateTicket = self.fieldtodatetime( v, adatefield, adateformat )
      cdateTicket = self.fieldtodatetime( v, cdatefield, cdateformat )
      # defaultvalue -> conf
      defworktime = 1
      if adateTicket:
        v._setextension( 'assigndiff', (dateNow - adateTicket ).days )
      if cdateTicket:
        v._setextension( 'closingdiff', (dateNow - cdateTicket ).days )
      if (cdateTicket!=None) and (adateTicket!=None):
        v._setextension( 'worktime', ( cdateTicket - adateTicket ).days )
      else:
        v._setextension( 'worktime', defworktime )
        ptimedelta = datetime.timedelta( days = defworktime )
        if (cdateTicket!=None) or (adateTicket!=None):
          if cdateTicket:
            adateTicket = cdateTicket - ptimedelta
          if adateTicket:
            cdateTicket = adateTicket + ptimedelta
          if ( not v.hasextension( 'assigndiff' ) ) or ( not v.hasextension( 'closingdiff' ) ):
            if v.hasextension( 'assigndiff' ):
              v._setextension( 'closingdiff', v.getextension( 'assigndiff' ) - defworktime )
            if v.hasextension( 'closingdiff' ):
              v._setextension( 'assigndiff', v.getextension( 'closingdiff' ) + defworktime )
      if (adateTicket!=None) and (cdateTicket!=None):
        ###### static workload calculation
        if ( v.getextension( 'assigndiff' ) > 0 ) or ( v.getextension( 'closingdiff' ) > 0 ):
          if v.getextension( 'assigndiff' ) > 0:
            ptimedelta = datetime.timedelta( days = v.getextension( 'assigndiff' ) )
            adateTicket = adateTicket + ptimedelta
            cdateTicket = cdateTicket + ptimedelta
          else:
            ptimedelta = datetime.timedelta( days = v.getextension( 'closingdiff' ) )
            cdateTicket = cdateTicket + ptimedelta
        ######
        v._setextension( 'startdate', adateTicket )
        v._setextension( 'finishdate', cdateTicket )

    return True

TSExtensionRegister.add( ppTSDueTimes, 'duetimediffs' )

# Berechnung fuer End und Start Ticket in die Kritische Pfadanalyse einfuegen
#  -- pseudotickets einfuegen
#  -- berechnung
#  -- pseudotickets wieder entfernen und dependencies/reversedependencies/start/ende in ticketset extension feldern speichern
#    das ermoeglicht es die abhaengigkeiten in den grapviz renderern nachtraeglich einzubauen
class ppTSCriticalPathSimple( ppTicketSetExtension ):

  BETickets_Begin = 999999
  BETickets_End = 1000000

  def __init__(self,ticketset,ticketsetdata):
    self.__ts = ticketsetdata
    self.ticketset = ticketset
    self.ticketset.needExtension( 'dependencies' )
    self.ticketset.needExtension( 'reverse_dependencies' )
    self.ticketset.needExtension( 'duetimediffs' )

  def _inject_start_end(self ):
    '''
      Add Pseudo Project Begin and End Tickets
        - Begin Ticket has the Time t1 of earliest Ticket or
          now if now < t1
        - End Ticket has the Time t2 of latest Ticket or
          now if t2 < now
    '''
    # get the starting tickets
    starts = set()
    for k in self.__ts:
      if len(self.__ts[ k ].getextension( 'dependencies' )) <= 0:
        starts.add( self.__ts[ k ] )

    dateNow = datetime.datetime.today()
    # add the pseudo ticket
    dateStart = dateNow
    for t in starts:
      if t.hasextension( 'startdate' ) and (
           t.getextension( 'startdate' ) != None ) and (
           t.getextension( 'startdate' ) < dateStart ):
        dateStart = t.getextension( 'startdate' )
    if dateStart < dateNow:
      pseudostat = 'closed'
    else:
      pseudostat = 'new'
    pseudoticket = { 'id' : self.BETickets_Begin,
                     'status': pseudostat }
    self.ticketset.addTicket( pseudoticket )
    # add extensions to the new pseudo ticket
    ppstartticket = self.__ts[ self.BETickets_Begin ]
    ppstartticket._setextension( 'dependencies', set() )
    ppstartticket._setextension( 'reverse_dependencies', starts )
    ppstartticket._setextension( 'startdate', dateStart )
    ppstartticket._setextension( 'finishdate', dateStart )
    # fix dependencies for "old" starting tickets
    for t in starts:
      t.getextension( 'dependencies' ).add( ppstartticket )

    # reverse procedure for the end ticket
    ends = set()
    for k in self.__ts:
      if len(self.__ts[ k ].getextension( 'reverse_dependencies' )) <= 0:
        ends.add( self.__ts[ k ] )
    # add the pseudo ticket
    dateEnd = dateNow
    for t in ends:
      if t.hasextension( 'finishdate' ) and (
           t.getextension( 'finishdate' ) != None ) and (
           t.getextension( 'finishdate' ) > dateEnd ):
        dateEnd = t.getextension( 'finishdate' )
    pseudostat = 'new'
    pseudoticket = { 'id' : self.BETickets_End,
                     'status': pseudostat }
    self.ticketset.addTicket( pseudoticket )
    # add extensions to the new pseudo ticket
    ppendticket = self.__ts[ self.BETickets_End ]
    ppendticket._setextension( 'dependencies', ends )
    ppendticket._setextension( 'reverse_dependencies', set() )
    ppendticket._setextension( 'startdate', dateEnd )
    ppendticket._setextension( 'finishdate', dateEnd )
    # fix dependencies for "old" starting tickets
    for t in ends:
      t.getextension( 'reverse_dependencies' ).add( ppendticket )

  def _cleanup_start_end(self ):
    # prepare results - because both start and end are critical and buffers
    # are set in inner Tickets, the usefull data is time/dependencies
    result = { 'starts': self.__ts[ self.BETickets_Begin ].getextension( 'reverse_dependencies' ),
               'startdate': self.__ts[ self.BETickets_Begin ].getextension( 'startdate' ),
               'ends': self.__ts[ self.BETickets_End ].getextension( 'dependencies' ),
               'enddate': self.__ts[ self.BETickets_End ].getextension( 'finishdate' ) }
    # remove reverse_dependencies from starttickets (just empty them, they where empty before!)
    for t in result[ 'starts' ]:
      t._setextension( 'dependencies', set() )
    # same for end tickets + cleanup the mindepbuffer extension field which references the nonexisting endticket
    for t in result[ 'ends' ]:
      t._setextension( 'reverse_dependencies', set() )
      if t.hasextension( 'mindepbuffers' ):
        t._setextension( 'mindepbuffers', [] )
    # remove the pseudo tickets
    del self.__ts[ self.BETickets_Begin ]
    del self.__ts[ self.BETickets_End ]

    return result

  def extend(self):
    betickets = "betickets" in self.ticketset.macroenv.macroargs
    if betickets:
      self._inject_start_end()
    # pass 1, check for start and finish dates
    for k in self.__ts:
      v = self.__ts[ k ]
      if (not v.hasextension( 'startdate' )) or (not v.hasextension( 'finishdate' )):
        if betickets:
          self._cleanup_start_end()
        return False
    # pass 2. get the first nodes for topological run
    queue = []
    for k in self.__ts:
      if len(self.__ts[ k ].getextension( 'dependencies' )) <= 0:
        queue.append( k )
    # pass 3. breadth first topological run, calculate buffer times per dependency
    while len(queue)>0:
      current = queue.pop(0)
      if not self.__ts[ current ].hasextension( 'depbuffers' ):
        deps = self.__ts[ current ].getextension( 'reverse_dependencies' )
        depbuffers = []
        for d in deps:
          if d.getfielddef( 'status', '' )!='closed':
            if self.__ts[ current ].getfielddef( 'status', '' )!='closed':
              depbuffer = ( d.getfield('id'), ( d.getextension( 'startdate' ) - self.__ts[ current ].getextension( 'finishdate' ) ).days )
            else:
              depbuffer = ( d.getfield('id'), ( d.getextension( 'startdate' ) - self.__ts[ current ].getextension( 'startdate' ) ).days )
          else:
            depbuffer = ( d.getfield('id'), 0 )
          depbuffers.append( depbuffer )
          queue.append( d.getfield('id') )
        self.__ts[ current ]._setextension( 'depbuffers', depbuffers )
    # pass 4. get the first nodes for reverse run
    queue = []
    for k in self.__ts:
      if len(self.__ts[ k ].getextension( 'depbuffers' )) <= 0:
        queue.append( k )
    # pass 5. breadth first in reverse order, calculate the deps with min. cumulative buffers
    runtest = 0; # var for endless loop check (cyclic dependencies in graph)
    startnode_minbuffer = 36500
    while ( len(queue) > 0 ) and (runtest <= ( 3*len( queue ) ) ):
      current = queue.pop(0)

      if not self.__ts[ current ].hasextension( 'mindepbuffers' ):
        depbufs = self.__ts[ current ].getextension( 'depbuffers' )
        depbufsresolved = True
        for (k,buf) in depbufs:
          if not self.__ts[ k ].hasextension( 'mindepbuffers' ):
            depbufsresolved = False
            break
        if not depbufsresolved:
          # dependend buffermins are not calculated, recycle the current node for later testing
          queue.append( current )
          runtest = runtest +1
        else:
          runtest = 0
          for d in self.__ts[ current ].getextension( 'dependencies' ):
            queue.append( d.getfield('id') )
          mindepbuffers = []
          if len(depbufs)>0:
            minbuf = 36500
            for (k,buf) in depbufs:
              cbuf = ( buf + self.__ts[ k ].getextension( 'buffer' ) )
              if cbuf < minbuf:
                minbuf = cbuf
            self.__ts[ current ]._setextension( 'buffer', minbuf )
            if len(self.__ts[ current ].getextension( 'dependencies' )) <= 0:
              if minbuf < startnode_minbuffer:
                startnode_minbuffer = minbuf
            for (k,buf) in depbufs:
              cbuf = ( buf + self.__ts[ k ].getextension( 'buffer' ) )
              if cbuf <= minbuf:
                mindepbuffers.append( k )
          else:
            self.__ts[ current ]._setextension( 'buffer', 0 )
          self.__ts[ current ]._setextension( 'mindepbuffers', mindepbuffers )
      else:
        runtest = 0
    if len(queue) > 0:
      raise Exception( " Cyclic dependencies found, fix dependencies or remove critical path analysis " )
      #return False
    # pass 6. get the first nodes for min buffer pathes
    queue = []
    for k in self.__ts:
      if ( len(self.__ts[ k ].getextension( 'dependencies' )) <= 0 ) and ( self.__ts[ k ].getextension( 'buffer' ) <= startnode_minbuffer):
        queue.append( k )
    # pass 7. mark the critical path
    while len(queue) > 0:
      current = queue.pop(0)
      self.__ts[ current ]._setextension( 'critical', True )
      for d in self.__ts[ current ].getextension( 'mindepbuffers' ):
        queue.append( d )

    # cleanup depbuffers
    for k in self.__ts:
      if self.__ts[ k ].hasextension( 'depbuffers' ):
        self.__ts[ k ]._delextension( 'depbuffers' )

    if betickets:
      return self._cleanup_start_end()
    else:
      return True

TSExtensionRegister.add( ppTSCriticalPathSimple, 'criticalpath_simple' )

