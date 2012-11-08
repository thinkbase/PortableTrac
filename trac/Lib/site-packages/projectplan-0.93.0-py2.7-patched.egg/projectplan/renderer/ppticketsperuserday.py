# -*- coding: utf-8 -*-

'''
  ALPHA
  TODO: extend the statistics within the footer of the table
'''


import string
import datetime
import time
from genshi.builder import tag
from genshi.input import HTMLParser
from genshi.core import Stream as EventStream, Markup
from genshi.template.markup import MarkupTemplate

from pprenderimpl import RenderImpl
from trac.web.chrome import add_stylesheet, add_script

class TicketsPerUserDay(RenderImpl):
  '''
    render a table
  '''
  fielddefault = 'status'
  weekdays = ['mo', 'tu', 'we', 'th', 'fr', 'sa', 'su' ]
  FRAME_LABEL = 'Table: Tickets of User per Day'
  
  def __init__(self,macroenv):
    '''
      Initialize
    '''
    self.macroenv = macroenv
    
    cols = self.macroenv.macrokw.get('cols') # standard parameter
    coltype = self.macroenv.macrokw.get('coltype') # standard parameter
    
    if cols == None:
      # for backward compatibility
      segments = self.macroenv.macrokw.get('segments') 
      if segments == None:
        self.segments = []
      else:
        self.segments = [ self.parseTimeSegment(s.strip()) for s in segments.split(';') ] 
    
    
    rows = self.macroenv.macrokw.get('rows') # standard parameter
    rowtype = self.macroenv.macrokw.get('rowtype') # standard parameter
    
    # backward compatibility
    if rows == None :
      rows = self.macroenv.macrokw.get('owners') # left for legacy reasons
      rowtype = 'owner' # left for legacy reasons
    
    self.rowtype = rowtype
    if rows == None :
      self.rows = []
    else:
      self.rows = [ o.strip() for o in rows.split(';') ] 
    
    cssclass = self.macroenv.macrokw.get('cssclass')
    if cssclass == None:
      self.cssclass = 'blacktable' # fallback
    else:
      self.cssclass = cssclass.strip()
    
    
    showsummary = self.macroenv.macrokw.get('summary')
    self.showsummarypiechart = False
    
    if showsummary == None:
      pass # fallback
    else:
      showsummary = showsummary.lower()
      if showsummary == 'chart' : 
        self.showsummarypiechart = True # default
      elif showsummary == 'chart:pie':
        self.showsummarypiechart = True
      else:
        pass

    self.statistics_class = '' # default
    try:
      #self.macroenv.tracenv.log.error('fields: '+self.macroenv.macrokw.get('statistics'))
      tmp = self.macroenv.macrokw.get('statistics').split('/')
      self.statistics_fields = []
      for field in tmp:
        try:
          if field != None and field != '' and field.strip() != '':
            self.statistics_fields.append(field.strip())
        except:
          pass
      self.statistics_class = 'pptableticketperday'
    except Exception,e:
      self.macroenv.tracenv.log.warning(repr(e))
      self.statistics_fields = [] # fallback
    
    
    self.isShowAggregatedTicketState = self.macroenv.get_bool_arg('showaggregatedstate', False)
    

  def isSummary( self ):
    return self.showsummarypiechart or False # add other values
  
  def showAggregatedTicketState( self ):
    return self.isShowAggregatedTicketState or False

  def getHeadline( self ):
    title = self.getTitle()
    if title != None:
      return('%s: %s' % (self.FRAME_LABEL,title))
    else:
      return('%s' % (self.FRAME_LABEL,))

  def render_statistics(self,ticketlist):
    # fallback if preconditions are not holding
    if len(ticketlist) == 0 or self.statistics_fields == []:
      return tag.span()
    
    # create a new map 
    statistics_values = {}
    for field in self.statistics_fields:
      statistics_values[field] = 0
    
    # map containing titles
    field_titles = {}
    for field in self.statistics_fields:
      field_titles[field] = 'sum of "%s"' % (field,)
    
    # summarize the field values of each ticket
    html = tag.div()
    for ticket in ticketlist:
      for field in self.statistics_fields:
        try:
          statistics_values[field] += int(ticket.getfield(field))
        except:
          field_titles[field] = '"%s" could not be parsed to number' % (field,)

    # create html construct
    separator = ''
    for field in self.statistics_fields:
      html(separator, tag.span('%s' % (statistics_values[field],), title=field_titles[field]) )
      separator = '/'

    return tag.div(html, class_='pptableticketperdaystatistics')

  def render(self, ticketset):
    '''
      Generate HTML List
      TODO: improve computation of ticket set
    '''
    orderedtickets = {}
    field = 'due_close'
    weekdays = ['PLACEHOLDER', 'Mo','Tu','We','Th','Fr','Sa','Su']
    
    r = ''
    div = tag.div()
    
    div(class_=self.cssclass+' projectplanrender' )
    
    # check for missing parameters 
    missingparameter = False
    if self.rows == [] :
      div(tag.div('Missing parameter "rows": use a semicolon-separated list to input the "'+self.rowtype+'".', class_='ppwarning')) 
      missingparameter = True
    if self.rowtype == None or  str(self.rowtype).strip() == '':
      div(tag.div('Missing parameter "rowtype": specifies the ticket attribute that should be showed.', class_='ppwarning')) 
      missingparameter = True
    if self.segments == [] :
      div(tag.div('Missing parameter: use a semicolon-separated list to input the "segments".', class_='ppwarning'))
      missingparameter = True
    if missingparameter:
      return div
    
    # init the matrix
    for segment in self.segments :
      orderedtickets[segment] = {}
      for o in self.rows:
        orderedtickets[segment][o] = []
    
    # fill up matrix
    self.macroenv.tracenv.log.debug('number of tickets: '+str(len(ticketset.getIDList())) )
    for tid in ticketset.getIDList():
      try:
        ticket = ticketset.getTicket(tid)
        orderedtickets[ticket.getfield(field)][ticket.getfield(self.rowtype)].append(ticket)
      except Exception,e:
        self.macroenv.tracenv.log.debug('fill up matrix: #'+str(tid)+' '+repr(e))
        pass
    
    calendar = {}
    counttickets = {}
    currentDate = datetime.date.today()
    
    self.macroenv.tracenv.log.debug(repr(orderedtickets))
    table = tag.table( class_="data pptableticketperday" , border = "1", style = 'width:auto;')
    
    # standard values
    mystyle_org = ''
    mytitle_org = ''
    myclass_org = '' 
    
    # table header
    tr = tag.tr()
    tr(tag.th(tag.h4(self.rowtype)))
    # TODO: add today css class
    for segment in self.segments:
      mystyle = mystyle_org
      mytitle = mytitle_org
      myclass = myclass_org
      try:
        consideredDate = self.getDateOfSegment(segment)
        calendar[segment] = {}
        calendar[segment]['isocalendar'] = consideredDate.isocalendar()
        calendar[segment]['date'] = consideredDate
        subtitle = weekdays[calendar[segment]['isocalendar'][2]] + ', week '+str(calendar[segment]['isocalendar'][1])
        if consideredDate == currentDate:
          myclass = 'today' # overwrite
      except Exception,e:
        self.macroenv.tracenv.log.error(str(e)+' '+segment)
        calendar[segment]['isocalendar'] = (None, None, None)
        calendar[segment]['date'] = None
        subtitle = "--"
        mystyle = 'color:#000;'
        mytitle = 'date could not be resolved'
      tr(tag.th(tag.h4(segment, class_ = myclass ), tag.h5( subtitle, style = mystyle, title = mytitle, class_ = myclass  ))) 
      counttickets[segment] = 0
    if self.showsummarypiechart:
      tr(tag.th(tag.h4('Summary', class_ = myclass_org ), tag.h5( 'of all tickets', style = mystyle_org, title = mytitle_org, class_ = myclass_org ))) 
    table(tag.thead(tr)) # Summary
    
    self.macroenv.tracenv.log.debug('tickets in table: '+repr(orderedtickets))
    
    
    # table body
    tbody = tag.tbody()
    counter=0
    
    for o in self.rows:
      if counter % 2 == 1:
        class_ = 'odd'
      else:
        class_ = 'even'
      counter += 1
      tr = tag.tr(class_ = class_)
      
      tr( tag.td(tag.h5(tag.a( o, href=self.macroenv.tracenv.href()+('/query?%s=%s&order=status' % (self.rowtype,o,)) )))) # query owner's tickets
      countStatus = {} # summarize the status of a ticket 
      for segment in self.segments:
        class_ = ''
        if calendar[segment]['date'] == currentDate: # Today
          class_ = 'today'
        elif calendar[segment]['isocalendar'][2] == 6: # Saturday
          class_ = 'saturday'
        elif calendar[segment]['isocalendar'][2] == 7: # Sunday
          class_ = 'sunday'
        td_div = tag.div()
        
        
        # only show the highlight, if the date is in the past
        color_class = ''
        if  self.showAggregatedTicketState()  and  calendar[segment]['date'] < currentDate:
          # determine color 
          state_new = 1
          state_work = 2
          state_done = 3
          state_none = 4
          
          state_progess = state_none
          
          for ticket in orderedtickets[segment][o]:
            status = ticket.getfield('status')
            if status in ['in_QA','closed'] and state_progess >= state_done:
              state_progess = state_done
            elif status in ['in_work','assigned','infoneeded'] and state_progess >= state_work:
              state_progess = state_work
            elif status in ['new','infoneeded_new'] and state_progess >= state_new:
              state_progess = state_new
          
          color_class =  { # switch/case in Python style
            state_none: '',
            state_new: 'bar bar_red',
            state_work: 'bar bar_blue',
            state_done: 'bar bar_green'
          }.get(state_progess, '')
        
        
        
        for ticket in orderedtickets[segment][o]:
          counttickets[segment] += 1
          td_div(tag.div( tag.span(self.createTicketLink(ticket), class_ = 'ticket_inner') ) )
          
          if ticket.getfield('status') in countStatus.keys(): # count values
            countStatus[ticket.getfield('status')] += 1
          else:
            countStatus[ticket.getfield('status')] = 1
        
        #tr(tag.td( tag.div( td_div, style = 'border-left:3px solid %s;' % (color) ) ) )
        tr(tag.td( tag.div( td_div ), self.render_statistics(orderedtickets[segment][o]), class_ = '%s %s %s' % (color_class, class_, self.statistics_class)  ) )
      if self.showsummarypiechart:
        tr(tag.td(tag.img(src=self.createGoogleChartFromDict('ColorForStatus', countStatus)))) # Summary
      tbody(tr)
    table(tbody)
    
    countTickets = 0
    tfoot = tag.tfoot()
    tr = tag.tr()
    tr(tag.td(tag.h5(self.rowtype+': '+str(len(self.rows)))))
    for segment in self.segments:
      tr(tag.td(tag.h5(str(counttickets[segment])+' tickets')))
      countTickets += counttickets[segment]
    if self.showsummarypiechart:
      tr(tag.td(tag.h5(str(str(countTickets))+' tickets'))) # Summary
    tfoot(tr)
    table(tfoot)
    
    div(table)
    return div



class TicketTableAvsB(RenderImpl):
  '''
    rewritten class of TicketsPerUserDay
    generic approach to show the tickets over two dimensions
    examples: 
      [[ProjectPlan(renderer=tableavsb,rowtype=component,rows=X;Y,coltype=owner,cols=A;B)]]
      [[ProjectPlan(renderer=tableavsb,rowtype=component,rows=X;Y,coltype=owner,cols=A;B, summary=chart)]]
      [[ProjectPlan(renderer=tableavsb,rowtype=component,rows=X;Y|Z|Q,coltype=owner,cols=A|B;C)]]
    TODO: allow multiple col/row values, like coltype=priority, cols=minor|trivial;major
  '''
  def __init__(self,macroenv):
    '''
      Initialize
    '''
    self.macroenv = macroenv
    
    self.coltype = self.macroenv.macrokw.get('coltype') # standard parameter
    if self.macroenv.macrokw.get('cols') != None :
      self.cols = [ s.strip() for s in self.macroenv.macrokw.get('cols').split(';') ]     # standard parameter
      self.cols = [ s.split('|') for s in self.cols ]
    else :
      self.cols = None
    
    self.rowtype = self.macroenv.macrokw.get('rowtype') # standard parameter
    if self.macroenv.macrokw.get('rows') != None :
      self.rows = [ s.strip() for s in self.macroenv.macrokw.get('rows').split(';') ]     # standard parameter
      self.rows = [ s.split('|') for s in self.rows ]
    else :
      self.rows = None
    
    cssclass = self.macroenv.macrokw.get('cssclass')
    if cssclass == None:
      self.cssclass = 'blacktable' # fallback
    else:
      self.cssclass = cssclass.strip()
    
    # init flag for charts summary
    showsummary = self.macroenv.macrokw.get('summary')
    self.showsummarypiechart = False
    if showsummary == None:
      pass # fallback
    else:
      showsummary = showsummary.lower()
      if showsummary == 'chart' : 
        self.showsummarypiechart = True # default
      elif showsummary == 'chart:pie':
        self.showsummarypiechart = True
      else:
        pass
    


  def render(self, ticketset):
    return_div = tag.div(class_=self.cssclass+' projectplanrender' )
    
    # check for missing parameters 
    missingparameter = False
    if self.rows == [] or self.rows == None:
      return_div(tag.div('Missing parameter "rows": use a semicolon-separated list to input the "'+self.rowtype+'".', class_='ppwarning')) 
      missingparameter = True
    if self.rowtype == None or  str(self.rowtype).strip() == '':
      return_div(tag.div('Missing parameter "rowtype": specifies the ticket attribute that should be showed at the rows.', class_='ppwarning')) 
      missingparameter = True
    if self.cols == [] or self.cols == None:
      return_div(tag.div('Missing parameter: use a semicolon-separated list to input the "cols".', class_='ppwarning'))
      missingparameter = True
    if self.coltype == None or  str(self.coltype).strip() == '':
      return_div(tag.div('Missing parameter "coltype": specifies the ticket attribute that should be showed in the columns.', class_='ppwarning')) 
      missingparameter = True
    if missingparameter:
      return return_div
    
    
    #ul = tag.ul()
    #for tid in ticketset.getIDSortedList():
      #ticket = ticketset.getTicket(tid)
      #ul( tag.li(tid, " ",ticket.getfield('component') , " ", ticket.getfield('owner') ))
    #return_div(ul)
    def getstatistictitle( statusdict ):
      mytitle = ''
      mysum = 0
      for status in statusdict:
        mytitle += "%s: %s\n" % (status, str(statusdict[status]) )
        mysum += int(statusdict[status])
      mytitle += "%s: %s" % ('number', mysum)
      return mytitle
    
    def setKV( myStruct, myKey, newValue ):
      '''
        shortcut to set the values correctly
        used to reduce the code needed while using a list as key of a dict
      '''
      myStruct[str(myKey)] = newValue
    
    def tableKeyPrettyPrint( mylist ) :
      '''
        transform a list of keys to a user readable string
        in: ['a','b'] --> out: 'a|b'
      '''
      return '|'.join(mylist)
    
    def tableKeyQueryParameter( parameter, mylist ) :
      '''
        transform a list of keys to a Trac query string parameter  (OR)
        in: x, ['a','b'] --> out: 'x=a&x=b'
      '''
      return '&'.join([ "%s=%s" % (parameter, s) for s in mylist ])
    
    
    chartheight=80
    chartwidth=170
    
    data = {}
    statistics = {}
    
    # init table data 
    for row in self.rows :
      colstatistics = {}
      colkeys = {}
      for col in self.cols :
        # colkeys[col] = []
        setKV( colkeys, col, [] )
        # colstatistics[col] = {}
        setKV( colstatistics, col, {} )
      # data[row] = colkeys
      setKV( data, row, colkeys )
      # statistics[row] = colstatistics
      setKV( statistics, row, colstatistics )
    
    for tid in ticketset.getIDSortedList():
      ticket = ticketset.getTicket(tid)
      ticket_rowtype = ticket.getfield(self.rowtype)
      ticket_coltype =  ticket.getfield(self.coltype)
      
      # determine the data cell where the ticket has to be added, keep in mind that rows and cols are list of lists
      for row in self.rows :
        for col in self.cols :
          if ticket_rowtype in row and ticket_coltype in col :
            data[str(row)][str(col)].append(ticket) # save tickets at precise values of row and col
            self.log_debug('row:%s col:%s append:%s' % (row,col,tid))
      
      # if ticket_rowtype in self.rows and ticket_coltype in self.cols :
    
    # create HTML table
    table = tag.table( class_="data pptableticketperday" , border = "1", style = 'width:auto;')
    
    # create HTML table head
    thead = tag.thead()
    tr = tag.tr()
    tr( tag.th("%s vs %s" % (self.rowtype,self.coltype) ) )
    for colkey in self.cols :
      tr( tag.th(tag.h4(tag.a( tableKeyPrettyPrint(colkey), href=self.macroenv.tracenv.href()+('/query?%s&order=%s' % ( tableKeyQueryParameter(self.coltype, colkey),self.rowtype)) )),title="%s is %s" % (self.coltype, tableKeyPrettyPrint(colkey) ) ) ) # first line with all colkeys
    if self.showsummarypiechart:
      tr( tag.th(tag.h4( "Ticket Overview" ) ) )  
    thead(tr)
    table(thead)
    
    # create HTML table body
    tbody = tag.tbody()
    counter=0
    
    for rowkey in self.rows :
      # switch line color
      if counter % 2 == 1:
        class_ = 'odd'
      else:
        class_ = 'even'
      counter += 1
      tr = tag.tr( class_=class_ ) # new line
      
      td = tag.td() # new cell
      td(tag.h5(tag.a( tableKeyPrettyPrint(rowkey), href=self.macroenv.tracenv.href()+('/query?%s&order=%s' % ( tableKeyQueryParameter( self.rowtype,rowkey),self.coltype)) )),title="%s is %s" % (self.rowtype, tableKeyPrettyPrint(rowkey) ) ) # first cell contains row key
      tr(td)
      for colkey in self.cols :
        td = tag.td()
        for ticket in data[str(rowkey)][str(colkey)] :
          td( tag.span(self.createTicketLink(ticket), class_ = 'ticket_inner' ), " " , mytitle="%s is %s and %s is %s" % (self.rowtype,rowkey,self.coltype,colkey) ) # mytitle might be used later by javascript
          if not statistics[str(rowkey)][str(colkey)].has_key( ticket.getstatus() ) :
            statistics[str(rowkey)][str(colkey)][ticket.getstatus()] = 0
          statistics[str(rowkey)][str(colkey)][ticket.getstatus()] += 1
        tr(td)
      
      # compute statistics
      rowstatistics = {}
      count = 0
      for colkey in statistics[str(rowkey)] :
        for status in statistics[str(rowkey)][str(colkey)] :
          if not rowstatistics.has_key(status) : 
            rowstatistics[status] = 0
          try:
            rowstatistics[status] += statistics[str(rowkey)][str(colkey)][status]
            count += statistics[str(rowkey)][str(colkey)][status]
          except:
            pass
        
      if self.showsummarypiechart:
        tr(tag.td(tag.img(src=self.createGoogleChartFromDict('ColorForStatus', rowstatistics, '%s tickets' % (count,), height=chartheight )), class_='ppstatistics' , title=getstatistictitle(rowstatistics)) ) # Summary
      
      tbody(tr)
    table(tbody)
    
    # create HTML table foot
    if self.showsummarypiechart :
      fullstatistics = {}
      tfoot = tag.tfoot()
      tr = tag.tr()
      
      tr( tag.td(tag.h5('Ticket Overview') ) )
      
      # create statistics for col
      fullcount = 0
      for colkey in self.cols :
        colstatistics = {}
        colcount = 0
        for rowkey in self.rows :
          for status in statistics[str(rowkey)][str(colkey)] :
            if not fullstatistics.has_key(status) : 
              fullstatistics[status] = 0
            if not colstatistics.has_key(status) : 
              colstatistics[status] = 0
            try:
              colstatistics[status] += statistics[str(rowkey)][str(colkey)][status]
              colcount += statistics[str(rowkey)][str(colkey)][status]
              fullstatistics[status] += statistics[str(rowkey)][str(colkey)][status]
              fullcount += statistics[str(rowkey)][str(colkey)][status]
            except:
              pass
        tr(tag.td(tag.img(src=self.createGoogleChartFromDict('ColorForStatus', colstatistics, '%s tickets' % (colcount,), height=chartheight)), title=getstatistictitle(colstatistics) )) # Col Summary
      tr(tag.td(tag.img(src=self.createGoogleChartFromDict('ColorForStatus', fullstatistics, '%s tickets' % (fullcount,), height=chartheight)), class_='ppstatistics', title=getstatistictitle(fullstatistics))) # Full Summary
      tfoot(tr)
      table(tfoot)
    
    return_div(table)
    
    return return_div 




