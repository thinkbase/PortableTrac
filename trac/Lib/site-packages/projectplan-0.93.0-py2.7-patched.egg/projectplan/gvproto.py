# -*- coding: utf-8 -*-

import os

import ppenv
from pputil import *

class NodePrototype():
  '''
    Node Prototype for Graphviz DOT Label HTML (a small and somewhat special
    subset of HTML)
  '''
  def __init__( self, macroenv ):
    '''
      Initialize an empty Node and the Tag stack
    '''
    self.macroenv = macroenv
    self.node = ''
    self.outrostack = []
    self.imgpath = ppenv.PPImageSelOption.absbasepath()
    self.color2 = '#E5E5E5'

  def _codeargs( self, **kwargs ):
    '''
      Write 'Argument="Value"' pairs into the Nodestring.
      This is for easy writing of Attributes from kwargs.
    '''
    nstring = ''
    for ( key, val ) in kwargs.items():
      addparameter = True
      
      if key.upper() == 'TITLE' or key.upper() == 'ALT':
        val = htmlspecialchars(val)
      if (key.upper() == 'COLOR' or key.upper() == 'BGCOLOR') and str(val).upper() == 'NONE':
        #self.macroenv.tracenv.log.warning(' _codeargs %s: %s = %s' % (self.ticket.getfield('id'), key, val) )
        addparameter = False
      
      if addparameter:
        nstring += '%s="%s" ' % ( key.upper(), val )
      
    return nstring

  def entertable( self, **kwargs ):
    '''
      Create an Opening TABLE Tag, write the Attributes and
      push the Closing Tag on stack.
    '''
    if len( kwargs ) > 0:
      self.node += '<TABLE ' + self._codeargs( **kwargs ) + '>'
    else:
      self.node += '<TABLE>'
    self.outrostack.append( "</TABLE>\n" )

  def entertr( self , **kwargs ):
    '''
      Create an Opening TR (Tablerow) Tag and push the Closing Tag on stack.
    '''
    if len( kwargs ) > 0:
      self.node += '<TR ' + self._codeargs( **kwargs ) + ' >'
    else:
      self.node += '<TR>'
    self.outrostack.append( '</TR>' )

  def entertd( self, **kwargs ):
    '''
      Create an Opening TD (Tablecell/column) Tag, write the Attributes and
      push the Closing Tag on stack.
    '''
    if len( kwargs ) > 0:
      self.node += '<TD ' + self._codeargs( **kwargs ) + ' >'
    else:
      self.node += '<TD>'
    self.outrostack.append( '</TD>' )

  def enterfont( self, color = "", face = "", size = "" ):
    '''
      Create an Opening FONT Tag, write the Attributes and
      push the Closing Tag on stack.
    '''
    self.node += '<FONT'
    if color != "":
       self.node += ' COLOR="%s"' % color
    if face != "":
       self.node += ' FACE="%s"' % face
    if size != "":
       self.node += ' POINT-SIZE="%s"' % size
    self.node += '>'
    self.outrostack.append( '</FONT>' )

  def enterimg( self, **kwargs ):
    '''
      Create an Opening IMG Tag, write the Attributes and
      push the Closing Tag on stack.
    '''
    if len( kwargs ) > 0:
      self.node += '<IMG ' + self._codeargs( **kwargs ) + ' >'
    else:
      self.node += '<IMG>'
    self.outrostack.append( '</IMG>' )

  def enterbr( self, **kwargs ):
    '''
      Create an Opening BR (Linebreak) Tag and write the Attributes.
    '''
    if len( kwargs ) > 0:
      self.node += '<BR ' + self._codeargs( **kwargs ) + ' >'
    else:
      self.node += '<BR>'

  def leave( self, num = 1 ):
    '''
      Write num Closing Tags from Stack into the Nodestring.
    '''
    while num > 0:
      self.node += self.outrostack.pop()
      num -= 1

  def leaveall( self ):
    '''
      Write all Closing Tags from Stack into the Nodestring.
    '''
    self.leave( len( self.outrostack ) )

  def addmarkup( self, instr ):
    '''
      Write an arbitrary string into the Nodestring, use the string might contain html markup
    '''
    self.node = self.node + instr + '\n'
    
  def add( self, instr ):
    '''
      Write an arbitrary string into the Nodestring, applies htmlspecialchars to generate a safe html string
    '''
    self.node = self.node + htmlspecialchars(instr) + '\n'
    
  def closeimg(self):
    '''
      draw a closing image
    '''
    # TODO: make configurable
    self.enterimg(src = os.path.join( self.imgpath, 'crystal_project/16x16/plusminus/viewmag-.png'))
    self.leave()

  def openimg(self):
    '''
      draw a opening image
    '''
    # TODO: make configurable
    self.enterimg(src = os.path.join( self.imgpath, 'crystal_project/16x16/plusminus/viewmag+.png'))
    self.leave()

  def render( self ):
    '''
      Return the Nodestring.
    '''
    return self.node

class TicketNodePrototype( NodePrototype ):
  '''
    Base Prototype for Ticket Nodes
    Creates HTML Code for GV Nodelabels
  '''

  TICKET_CLOSED_TO_LATE = 0
  TICKET_CLOSED_TO_EARLY = 1
  TICKET_CLOSED_ON_TIME = 2
  TICKET_CLOSED_NO_TIME = 3
  TICKET_OPEN_TO_LATE = 4
  TICKET_OPEN_TO_EARLY = 5
  TICKET_OPEN_DUE_TODAY = 6
  TICKET_OPEN_NO_TIME = 7


  def __init__( self, macroenv, ticket ):
    '''
      Initialize the Node Prototype and set usefull Vars.
    '''
    NodePrototype.__init__( self, macroenv )

    # get often used fields
    self.ticket = ticket
    self.ticketid = str( ticket.getfield( 'id' ) )
    self.tickettype = ticket.getfield( 'type' )
    self.ticketstatus = ticket.getfield( 'status' )
    self.ticketpriority = ticket.getfield( 'priority' )
    self.ticketuser = ticket.getfield( 'owner' )
    self.tickettype = ticket.getfield( 'type' )

    # get node color and image args
    self.fillcolor = self.macroenv.conf.get_map_val('ColorForStatus', self.ticketstatus )
    self.priocolor = self.macroenv.conf.get_map_val('ColorForPriority', self.ticketpriority )
    self.statuscolor = self.macroenv.conf.get_map_val('ColorForStatus', self.ticketstatus )
    self.typecolor = self.macroenv.conf.get_map_val('ColorForTicketType', self.tickettype )
    self.ticketnrcolor = self.color2
    #self.imgpath = ppenv.PPImageSelOption.absbasepath()

    # status image
    if self.macroenv.conf.get_map_val('ImageForStatus', self.ticketstatus ) != 'none':
      self.statusim = '<IMG SRC="' + os.path.join( self.imgpath,
        self.macroenv.conf.get_map_val('ImageForStatus', self.ticketstatus ) 
      ) + '"></IMG>'
    else:
      self.statusim = self.ticketstatus

    # status image
    if self.macroenv.conf.get_map_val('ImageForTicketType', self.tickettype ) != 'none':
      self.tickettypeim = '<IMG SRC="' + os.path.join( self.imgpath,
        self.macroenv.conf.get_map_val( 'ImageForTicketType', self.tickettype ) 
      ) + '"></IMG>'
    else:
      self.tickettypeim = self.tickettype

    # connector image
    connectorfallback = ppenv.PPEnv.connectimg # currently only one value needed
    # TODO: complete implementation
    if False and self.macroenv.conf.get_map_val(
         'ImageForConnector', connectorfallback ) != 'none':
      self.connectorim = '<IMG SRC="' + os.path.join( self.imgpath,
        self.macroenv.conf.get_map_val(
          'ImageForConnector', connectorfallback ) ) + '"></IMG>'
    else:
      self.connectorim = '<IMG SRC="' + os.path.join( self.imgpath, connectorfallback )+'" ></IMG>'

    # priority image
    if self.macroenv.conf.get_map_val(
         'ImageForPriority', self.ticketpriority ) != 'none':
      self.priorityim = '<IMG SRC="' + os.path.join( self.imgpath,
        self.macroenv.conf.get_map_val(
          'ImageForPriority', self.ticketpriority ) ) + '"></IMG>'
    else:
      self.priorityim = self.ticketpriority

    multiple = self.ticketuser.split(',')
    contained_in_multiple_user = False
    if len(multiple) >= 2:
      #self.macroenv.tracenv.log.warning('>= 2 users: %s, %s' % (self.ticketuser, multiple) )
      try:
        multiple.index(self.macroenv.tracreq.authname)
        contained_in_multiple_user = True
      except:
        pass

    # user image (owner indicator)
    if self.ticketuser == self.macroenv.tracreq.authname or contained_in_multiple_user:
      imgopt = 'ticket_owned_image'
      self.usercolor = self.macroenv.conf.get( 'ticket_owned_color' )
    else:
      imgopt = 'ticket_notowned_image'
      self.usercolor = self.macroenv.conf.get( 'ticket_notowned_color' )
    if self.macroenv.conf.get( imgopt ) != 'none':
      self.userim = '<IMG SRC="' + os.path.join( self.imgpath,
        self.macroenv.conf.get( imgopt ) ) + '"></IMG>'
    else:
      self.userim = self.ticketuser

    # if multiple users exist, then add a different image, however keep the color
    if len(multiple) >= 2 :
      imgopt = 'ticket_multiple_owner_image'
      userim = self.macroenv.conf.get( imgopt )
      self.macroenv.tracenv.log.warning('>= 2 users: %s, %s, %s' % (self.ticketuser, multiple,userim) )
      if userim != 'none':
        self.userim = '<IMG SRC="' + os.path.join( self.imgpath, userim ) + '"></IMG>'

    # set colwide for rows
    self.maxcolwide = 6


  def getdateclassification( self ):
    '''
      returns a tuple with the state and due
    '''
    cd = self.ticket.getextension( 'closingdiff' )
    if self.ticketstatus == 'closed':
      if cd != None: 
        if cd > 0: # to late
          return (TicketNodePrototype.TICKET_CLOSED_TO_LATE, cd)
        elif cd < 0 :
          return (TicketNodePrototype.TICKET_CLOSED_TO_EARLY, cd)
        else:
          return (TicketNodePrototype.TICKET_CLOSED_ON_TIME, cd)
      else:# cd = None
        return (TicketNodePrototype.TICKET_CLOSED_NO_TIME, None)
    
    else: #if self.ticketstatus != 'closed':
      if cd != None:
        if cd > 0: # to late
          return (TicketNodePrototype.TICKET_OPEN_TO_LATE, cd)
        elif cd < 0 : # to early
          return (TicketNodePrototype.TICKET_OPEN_TO_EARLY, cd)
        else: # today
          return (TicketNodePrototype.TICKET_OPEN_DUE_TODAY, cd)
      else:
        return (TicketNodePrototype.TICKET_OPEN_NO_TIME, None)

  def getdateconf( self, dueclassification, cd):
    '''
      return markup information
    '''
    if cd != None and ( cd > 1 or cd < -1 ):
      days = 'days'
    else:
      days = 'day'
    if TicketNodePrototype.TICKET_CLOSED_TO_LATE == dueclassification :
      return (
        '#ffb6c2',  # lightpink
        '!', 
        'crystal_project/16x16/calendar/timespan.png', 
        'closed: '+str( cd ) + ' '+days+' to late'
      )
    if TicketNodePrototype.TICKET_CLOSED_TO_EARLY == dueclassification :
      return (
        '#98fa98' ,  # palegreen
        '', 
        'crystal_project/16x16/calendar/todo.png',  
        'closed: ' + str( 0 - cd ) + ' '+days+' earlier'
      )
    if TicketNodePrototype.TICKET_CLOSED_ON_TIME == dueclassification :
      return (
        '#98fa98' , # palegreen
        '', 
        'crystal_project/16x16/calendar/todo.png', 
        'closed: bang on time' 
      )
    if TicketNodePrototype.TICKET_CLOSED_NO_TIME == dueclassification :
      return ( None, None, None, None )
    if TicketNodePrototype.TICKET_OPEN_TO_LATE == dueclassification :
      return ( 
        self.macroenv.conf.get( 'ticket_overdue_color' ), 
        '!', 
        self.macroenv.conf.get( 'ticket_overdue_image' ), 
        'closed: ' + str( cd ) + ' '+days+' delayed' 
      )
    if TicketNodePrototype.TICKET_OPEN_TO_EARLY == dueclassification :
      return ( 
        self.macroenv.conf.get( 'ticket_ontime_color' ), 
        '', 
        self.macroenv.conf.get( 'ticket_ontime_image' ), 
        'open: ' + str( 0 - cd ) + ' '+days+' left' 
      )
    if TicketNodePrototype.TICKET_OPEN_DUE_TODAY == dueclassification :
      return (  
        '#9CF9F9',  # Turquoise
        '!', 
        'crystal_project/16x16/calendar/today.png', 
        'open: due today!' 
      )
    if TicketNodePrototype.TICKET_OPEN_NO_TIME == dueclassification :
      return ( None, None, None, None )

    return ('#FF00FF', 'ERR', 'error.png', 'ERROR' )  # fallback, default, should not happened

#return { # switch/case in Python style
        #str(TicketNodePrototype.TICKET_CLOSED_TO_LATE): (),
        #str(TicketNodePrototype.TICKET_CLOSED_TO_EARLY): ( ), 
        #str(TicketNodePrototype.TICKET_CLOSED_ON_TIME): ( ), 
        #str(TicketNodePrototype.TICKET_CLOSED_NO_TIME): (),
        #str(TicketNodePrototype.TICKET_OPEN_TO_LATE): ( ),
        #str(TicketNodePrototype.TICKET_OPEN_TO_EARLY): (  ),
        #str(TicketNodePrototype.TICKET_OPEN_DUE_TODAY): (),
        #str(TicketNodePrototype.TICKET_OPEN_NO_TIME): ()
        #}.get( str(dueclassification), ('#FF00FF', 'ERR', 'error.png', 'ERROR' ) ) # fallback, default, should not happened

  def adddatecol( self ):
    '''
      returns column with date information
    '''
    (ticketclass, diff) = self.getdateclassification()
    (color, textshort, image, dueline) = self.getdateconf(ticketclass, diff)
    
    if color == None:  # due date is not contained in the ticket
      return
    else: 
      href = '?ticket_state?%s?state=%s' % (
             self.macroenv.tracreq.href( 'query' ), self.ticketstatus )
      self.entertd( title = dueline, href = href,
                  bgcolor = color , colspan = "1" )
      #self.entertd( title = dueline, href = "?ticket_inner?__dummy__", bgcolor = color )
     
      if  image != None:
        img = os.path.join( self.imgpath, image )
        self.enterimg( src = img )
        self.leave()
      else:
        # fall back if no image is defined
        self.addmarkup( '<FONT COLOR="#FFFF00">'+textshort+'</FONT>' )
     
      self.leave( 1 )


  def adddaterow( self ):
    '''
      returns row with date information
    '''
    ticketclass, diff = self.getdateclassification()
    color, textshort, image, dueline = self.getdateconf(ticketclass, diff)
    
    if color == None:  # due date is not contained in the ticket
      return
    else: 
      self.entertr()
      self.entertd( title = "due", href = "?ticket_inner?__dummy__", COLSPAN = str( self.maxcolwide), bgcolor = color )
      self.entertable(align = "center", cellpadding = "1", cellspacing = "0", border = "0")
      self.entertr()
      self.entertd()

      if  image != None:
        img = os.path.join( self.imgpath, image )
        self.enterimg( src = img )
        self.leave()
      else:
        # fall back if no image is defined
        self.addmarkup( '<FONT COLOR="#FFFF00">'+textshort+'</FONT>' )

      self.leave( 1 )
      self.entertd()
      self.add( dueline )
      self.leave( 5 )


  def addstatuscol( self ):
    '''
      Add a Status Column into the Node
    '''
    href = '?ticket_state?%s?state=%s' % (
             self.macroenv.tracreq.href( 'query' ), self.ticketstatus )
    self.entertd( title = 'state: '+self.ticketstatus, href = href,
                  bgcolor = self.statuscolor , colspan = "1" )
    self.addmarkup( self.statusim )
    self.leave()

  def addtickettypecol( self ):
    '''
      Add a Ticket Type Column into the Node
    '''
    href = '?ticket_state?%s?type=%s' % (
             self.macroenv.tracreq.href( 'query' ), self.ticketstatus )
    self.entertd( title = 'type: '+self.tickettype, href = href,
                  bgcolor = self.typecolor, colspan = "1" )
    self.addmarkup( self.tickettypeim )
    self.leave()

  def addconnectorcol( self ):
    '''
      Add a Connector Column into the Node
    '''
    href = 'javascript: return ppconnecttickets(%s); ' % ( self.ticketid )
    self.entertd( title = 'add/remove dependencies', href = href,
                  bgcolor = self.color2, colspan = "1" )
    self.addmarkup( self.connectorim )
    self.leave()

  def addprioritycol( self ):
    '''
      Add a Priority Column into the Node
    '''
    href = '?ticket_priority?%s?priority=%s' % (
             self.macroenv.tracreq.href( 'query' ), self.ticketpriority )
    self.entertd( title = 'priority: '+self.ticketpriority, href = href,
                  bgcolor = self.priocolor, colspan = "1" )
    self.addmarkup( self.priorityim )
    self.leave()

  def addownercol( self ):
    '''
      Add an Owner Column into the Node
    '''
    bgcol = self.usercolor
    href = '?ticket_owner?%s?owner=%s' % (
             self.macroenv.tracreq.href( 'query' ), self.ticketuser )
    self.entertd( title = 'user: '+self.ticketuser, bgcolor = bgcol,
                  href = href, color = self.color2, colspan = "1" )
    self.addmarkup( self.userim )
    self.leave()

  def addticketcol( self ):
    '''
      Add a Ticket Column into the Node
    '''
    self.entertd( title = "show ticket #" + self.ticketid, color = self.ticketnrcolor,
                  colspan = "1", align = "CENTER", valign = "MIDDLE", 
                  href = "?ticket_inner?" + self.ticket.getfield( 'href' ) )
    self.addmarkup( self.ticketid )
    self.leave()

  def addsummaryrow( self ):
    '''
      Add a Summary Row into the Node
    '''
    self.entertr()
    self.entertd( TITLE = "summary", BGCOLOR = "#FFFFFF",
                  COLOR = self.color2, COLSPAN = str( self.maxcolwide ) )
    summary = self.ticket.getfield( 'summary' )
    # ensure some space around the summary text 
    self.entertable( cellpadding = "2", cellspacing = "2", border = "0" )
    self.entertr()
    self.entertd()
    maxtext = 21
    if len( summary ) > maxtext:
      self.add( summary[ 0:(maxtext-2)] + '...' )
    else:
      self.add( summary )
    self.leave( 5 )

  def adddebugtimes( self ):
    '''
      Add Debug Information for Critical Path Analyses (Estimated Start/Finish and Buffer)
    '''
    # 3 rows for tmp debug infos
    if self.ticket.hasextension( 'startdate' ):
      self.entertr()
      self.entertd( TITLE = "startdate", BGCOLOR = "#FFFFFF",
                    COLOR = self.color2, COLSPAN = str( self.maxcolwide ) )
      self.add( 'ETS %s ' % self.ticket.getextension(
                        'startdate' ).strftime( "%d/%m/%y" ) )
      self.leave( 2 )

    if self.ticket.hasextension( 'finishdate' ):
      self.entertr()
      self.entertd( TITLE = "finishdate", BGCOLOR = "#FFFFFF",
                    COLOR = self.color2, COLSPAN = str( self.maxcolwide ) )
      self.add( 'ETF %s ' % self.ticket.getextension(
                        'finishdate' ).strftime( "%d/%m/%y" ) )
      self.leave( 2 )

    if self.ticket.hasextension( 'buffer' ):
      self.entertr()
      self.entertd( TITLE = "buffer", BGCOLOR = "#FFFFFF",
                    COLOR = self.color2, COLSPAN = str( self.maxcolwide ) )
      self.add( "Buffer in Days: %s " % str(
                        self.ticket.getextension( 'buffer' ) ) )
      self.leave( 2 )

  def renderhighlight_header( self ):
    '''
      start a frame, purpose: hightlight of this ticket
    '''
    # TODO: choose better colors
    
    if self.ticketid in self.macroenv.macrokw.get('highlightticket', '0').split(';') :
      self.entertable(border = 0, bgcolor = '#FFFFD7', cellspacing = 2, cellpadding = 0)
      self.entertr()
      self.entertd()
      self.entertable(border = 0, bgcolor = '#FFFFAF', cellspacing = 2, cellpadding = 0)
      self.entertr()
      self.entertd()
      self.entertable(border = 0,  bgcolor = '#FFFF87', cellspacing = 2, cellpadding = 0)
      self.entertr()
      self.entertd()
      self.entertable( border = 0, bgcolor = '#FFFF5F', cellspacing = 2, cellpadding = 0)
      self.entertr()
      self.entertd()
      self.entertable( border = 0, bgcolor = '#FFFFFF', cellspacing = 2, cellpadding = 0)
      self.entertr()
      self.entertd()

  def render( self ):
    '''
      Create and Return the Node Markup
    '''
    # table
    # cellpadding should be zero to avoid mouseover problems
    #self.entertable( align = "CENTER", bgcolor = self.fillcolor, border = "1",
    self.renderhighlight_header() # render has to be finished with leaveall
    
    self.entertable( align = "CENTER", border = "1",
                     cellborder = "0", cellpadding = "0", cellspacing = "2",
                     color = self.priocolor, title = "Ticket: " + self.ticketid,
                     bgcolor = self.color2,
                     valign = "MIDDLE", href = "?ticket?__dummy__" )
    # first row, |ticketnumer|status|owner|priority|
    self.entertr()
    self.addticketcol()
    self.addtickettypecol()
    self.addstatuscol()
    self.addconnectorcol()
    self.addownercol()
    self.addprioritycol()
    self.leave()
    # second row, ticket description (first 22 chars of short description)
    self.addsummaryrow()
    #self.adddebugtimes()
    # add due row
    self.adddaterow()
    # finish
    self.leaveall()

    return NodePrototype.render( self )



class TicketSimpleNodePrototype( TicketNodePrototype ):
  '''
    simple renderer for ticket nodes
    creates HTML code for GV nodelabels encoding only ticketnumber, ticketpriority and ticketstatus
    inspired by MasterTicketsPlugin (http://trac-hacks.org/wiki/MasterTicketsPlugin)
  '''

  def __init__( self, macroenv, ticket ):
    '''
      Initialize the Node Prototype and set usefull Vars.
    '''
    TicketNodePrototype.__init__( self, macroenv, ticket )
    self.ticketnrcolor = self.statuscolor


  def render( self ):
    '''
      Create and Return the Node Markup
    '''
    self.renderhighlight_header() # render has to be finished with leaveall
    
    self.entertable( align = "CENTER", border = "2",
                     cellborder = "0", cellpadding = "0", cellspacing = "2",
                     title = "Ticket: " + self.ticketid+ "(" + self.ticketstatus + " " + self.tickettype + ")",
                     color = self.priocolor,
                     bgcolor = self.statuscolor,
                     valign = "MIDDLE", href = "?ticket?__dummy__" )
    self.entertr()
    self.addticketcol()
    self.addstatuscol()
    self.adddatecol()
    self.leaveall()
    
    return NodePrototype.render( self )



class MilestoneNodePrototype( NodePrototype ):
  '''
    Base Prototype for Milestone Nodes
    Creates HTML Code for GV Nodelabels
  '''
  def __init__( self, macroenv, version, milestone, tickets, mtitlehref ):
    '''
      Initialize the Base Node Prototype.
    '''
    NodePrototype.__init__( self, macroenv )
    self.version = version
    self.milestone = milestone
    self.tickets = tickets
    self.href = mtitlehref

  def addtickettable( self ):
    '''
      Add a Table with Ticket per Due and per Status Information for this Milestone.
    '''
    statsmap = dict()
    delayedc = 0
    delayeda = 0
    intime = 0
    unknown = 0

    for t in self.tickets:
      s = t.getfielddef( 'status', '' )
      if s in statsmap:
        statsmap[ s ] += 1
      else:
        statsmap[ s ] = 1

      if s != 'closed':
        if t.hasextension( 'closingdiff' ) and (
             t.getextension( 'closingdiff' ) > 0 ):
          delayedc += 1
        elif t.hasextension( 'assigndiff' ) and (
               t.getextension( 'assigndiff' ) > 0 ):
          delayeda += 1
        else:
          if t.hasextension( 'closingdiff' ) and t.hasextension( 'assigndiff' ):
            intime += 1
          else:
            unknown += 1
      else:
        intime += 1

    if len( statsmap ) > 0:
      self.enterfont( color = '#000000', size = '10' )
      self.entertable( border = "0", cellborder = "1" )
      self.entertr()
      self.entertd( border = "0" )
      self.addmarkup( 'Tickets per Status' )
      self.leave( 2 )
      for ( key, val ) in statsmap.items():
        self.entertr()
        self.entertd( bgcolor = self.macroenv.conf.get_map_val(
                                  'ColorForStatus', key ) )
        if len( key ) > 0:
          self.add( key + ': ' + str( val ) )
        else:
          self.add( 'status unknown: ' + str( val ) )
        self.leave( 2 )
      if ( unknown > 0 ) or ( delayedc > 0 ) or ( delayeda > 0 ):
        self.entertr()
        self.entertd( border = "0" )
        self.addmarkup( 'Tickets per Due' )
        self.leave( 2 )
        def writeduecol( bgcol, text, num ):
          if num > 0:
            self.entertr()
            self.entertd( bgcolor = bgcol )
            self.add( text + ': ' + str( num ) )
            self.leave( 2 )
        writeduecol( '#FF0000', 'delayed closing', delayedc )
        writeduecol( '#FF0000', 'delayed assignment', delayeda )
        writeduecol( '#FFFF00', 'unknown', unknown )
        writeduecol( '#00FF00', 'on time', intime )
      self.leave( 2 )
    else:
      # that shouldn't ever happen, since gvrender/gvhierach only handles ms/ver with tickets
      self.entertr()
      self.entertd()
      self.addmarkup( 'no Tickets' )
      self.leave( 2 )

  def render( self ):
    '''
      Create and Return the Node Markup
    '''
    href = '?ticket?%s' % self.href
    self.enterfont( color = self.macroenv.conf.get( 'milestone_fontcolor' ), size = '10' )
    self.entertable( align = "CENTER",
                     bgcolor = self.macroenv.conf.get( 'milestone_fillcolor' ),
                     border = "1", cellborder = "1",
                     color = self.macroenv.conf.get( 'milestone_color' ),
                     title = 'Milestone: %s' % self.milestone,
                     valign = "MIDDLE", href = href )
    self.entertr()
    self.entertd()
    self.entertable( align = "CENTER", border = "0", cellborder = "0", cellpadding = "0" )
    self.entertr()
    self.entertd()
    self.openimg()
    self.leave( )
    self.entertd()
    self.add( ' Milestone: ' + self.milestone ) # open milestone
    self.leave( 5 )
    self.entertr()
    self.entertd()
    self.addtickettable()
    self.leaveall()
    return NodePrototype.render( self )

class VersionNodePrototype( NodePrototype ):
  '''
    Base Prototype for Version Nodes
    Creates HTML Code for GV Nodelabels
  '''
  def __init__( self, macroenv, version, milestones, vtitlehref ):
    '''
      Initialize the Base Node Prototype.
    '''
    NodePrototype.__init__( self, macroenv )
    self.version = version
    self.milestones = milestones
    self.href = vtitlehref

  def addcompletiontable( self ):
    '''
      Create a Table with Completion Information for the Milestones in this
      Version.
    '''
    msmap = dict()
    for ( milestone, ticketlist ) in self.milestones.items():
      num = 0
      comp = 0
      for t in ticketlist:
        if t.getfielddef( 'status', '' ) == 'closed':
          comp += 1
        num += 1
      if num > 0:
        msmap[ milestone ] = '%s: %s%% [%s/%s]' % (
          milestone, str( ( comp * 100 ) / num ), str( comp ), str( num ) )
      else:
        msmap[ milestone ] = '%s: Empty' % milestone

    self.enterfont( color = '#000000', size = '10' )
    self.entertable( border = "0", cellborder = "1" )
    self.entertr()
    self.entertd( border = "0" )
    self.addmarkup( 'Milestone Completeness' )
    self.leave( 2 )
    for ( k, v ) in msmap.items():
      self.entertr()
      self.entertd()
      self.add( v )
      self.leave( 2 )
    self.leave( 2 )

  def render( self ):
    '''
      Create and Return the Node Markup
    '''
    href = '?ticket?%s' % self.href
    self.enterfont( color = self.macroenv.conf.get( 'version_fontcolor' ),
                    size = '11' )
    self.entertable( align = "CENTER",
                     bgcolor = self.macroenv.conf.get( 'version_fillcolor' ),
                     border = "1", cellborder = "1",
                     color = self.macroenv.conf.get( 'version_color' ),
                     title = 'open version: %s' % self.version,
                     valign = "MIDDLE", href = href )
    self.entertr()
    self.entertd()
    # new table, header
    self.entertable( align = "CENTER", border = "0" , cellborder = "0" )
    self.entertr()
    self.entertd()
    self.openimg()
    self.leave()
    self.entertd()
    self.add( 'Version: ' + self.version ) # open version
    self.leave( 5 )
    self.entertr()
    self.entertd()
    self.addcompletiontable()
    self.leaveall()
    return NodePrototype.render( self )

class GVRenderProto():
  '''
    Class which has some Methods for Node Prototype instantiation.
    Currently theres no special use for this but it can support
    different Node Prototypes for future settings. (f.e. using different
    Ticket Node Prototypes for different Priorities or something like that)
  '''

  @classmethod
  def ticket_gen_markup( cls, macroenv, ticket ):
    '''
      Create and Return Markup for the Ticket ticket
    '''
    # choose between the different implementations
    #macroenv.tracenv.log.warning("ticket_gen_markup %s", macroenv.macroid )
    try:
      ticketstyle = macroenv.macrokw.get('ticketstyle').lower()
    except:
      ticketstyle = ''
    
    if (str(macroenv.macroid) in ['3']) or ( ticketstyle == 'small') : # first: deprecated style
      return TicketSimpleNodePrototype( macroenv, ticket ).render()
    elif ( ticketstyle == 'smallifclosed') and ( ticket.getfield('status') == 'closed' ) : # small visualization if ticket is closed
      macroenv.tracenv.log.debug("smallifclosed: #%s %s" % (repr(ticket.getfield('id')),repr(ticket.getfield('status'))) )
      return TicketSimpleNodePrototype( macroenv, ticket ).render()
    else : # style = normal
      return TicketNodePrototype( macroenv, ticket ).render()

  @classmethod
  def milestone_gen_markup( cls, macroenv, version,
                            milestone, tickets, mhref = None ):
    '''
      Create and Return Markup for the Milestone milestone in Version version and
      with Tickets tickets. mhref is a hypertext reference which should be used for
      the Milestone Table href (used for hierarchical renderer).
    '''
    return MilestoneNodePrototype( macroenv, version, milestone,
                                   tickets, mhref ).render()

  @classmethod
  def version_gen_markup( cls, macroenv, version, milestones, vhref = None ):
    '''
      Create and Return Markup for the Version version and its
      Milestones milestones. vhref is a hypertext reference which should be used for
      the Version Table href (used for hierarchical renderer).
    '''
    return VersionNodePrototype( macroenv, version, milestones, vhref ).render()
