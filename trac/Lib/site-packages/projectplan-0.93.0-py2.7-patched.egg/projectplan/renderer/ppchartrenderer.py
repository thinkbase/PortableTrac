# -*- coding: utf-8 -*-

'''
  beta
  TODO: starttime, endtime
'''


import string
import datetime
import time
import random
from genshi.builder import tag
from genshi.input import HTMLParser
from genshi.core import Stream as EventStream, Markup
from genshi.template.markup import MarkupTemplate

from pprenderimpl import RenderImpl
from trac.web.chrome import add_stylesheet, add_script

class ChartRenderer(RenderImpl):
  '''
    render a chart of values
    a javascript renderer is used
  '''
  fielddefault = 'status'
  TICKET_STATUS_FIELD = 'status' # constant: observes the ticket status change
  weekdays = ['mo', 'tu', 'we', 'th', 'fr', 'sa', 'su' ]
  FRAME_LABEL = 'Burn-down Chart'
  
  def __init__(self,macroenv):
    '''
      Initialize
    '''
    self.macroenv = macroenv

  def getHeadline( self ):
    title = self.getTitle()
    if title != None:
      return('%s: %s' % (self.FRAME_LABEL,title))
    else:
      return('%s (per %s)' % (self.FRAME_LABEL,self.segment))

 
  def getField( self ):
    '''
      returns the user configuration or default which field should be observed
    '''
    return self.macroenv.macrokw.get( 'field', self.fielddefault )

  def getNameOfRenderFrame(self): 
    return( 'ppburndown_chart_'+str(self.macroenv.macrokw.get( 'macroid', 'defaultid')) )

  def datetime2seconds( self, dt ):
    return time.mktime(dt.timetuple())

  def seconds2datetime( self, secs ):
    return(datetime.datetime.fromtimestamp(secs))

  def seconds2dayseconds( self, secs ):
    '''
      normalize the seconds per day, i.e. computes the seconds to 00:00:01 of the day
    '''
    return((secs % 86400) * 86400 + 1)

  def getDateString( self, mytime ) :
    '''
      input seconds, returns year month day space-separated
    '''
    def getFormatBySegment( myDateTime ):
      if self.segment in ['day']: # day segments
        return myDateTime.strftime("%Y-%m-%d")
      elif self.segment in ['week','twoweek']: # other segments, e.g.: weeks, 2weeks, ...
        firstDateTime = self.getFirstDate()
        diff = myDateTime.date() - firstDateTime.date()
        extraDays = diff.days % 7 
        extraWeeks = diff.days / 7 
        if self.segment in ['week']:
          extraWeeks = diff.days / 7 
          dayoffset = 6
        elif self.segment in ['twoweek']:
          extraWeeks = diff.days / 14 
          dayoffset = 13
        myDateTimeWeekStart = firstDateTime + datetime.timedelta(days=(extraWeeks*7)) # get start of week
        myDateTimeWeekEnd   = myDateTimeWeekStart + datetime.timedelta(days=dayoffset) # get end of week
        self.macroenv.tracenv.log.debug("diff: %s - %s --> %s / %s --> %s -- %s" % (myDateTime.date(),firstDateTime.date(),extraWeeks,extraDays, myDateTimeWeekStart, myDateTimeWeekEnd ))
        return "%s\n- %s" % (myDateTimeWeekStart.strftime("%Y-%m-%d"), myDateTimeWeekEnd.strftime("%Y-%m-%d") )
      elif self.segment in ['month']: 
        return myDateTime.strftime("%Y-%m")
      elif self.segment in ['year']: 
        return myDateTime.strftime("%Y")
      
    #return datetime.datetime.fromtimestamp(mytime).strftime("%Y-%m-%d %H:%M")
    if isinstance(mytime, float):
      return getFormatBySegment(datetime.datetime.fromtimestamp(mytime))
    elif isinstance(mytime, datetime.date) or isinstance(mytime, datetime.datetime) :
      return getFormatBySegment( mytime )
    else:
      raise Exception('Unknown date: %s' % (mytime,))

  def setKeyIfNotExists( self, mylist, newkey ):
    '''
      call-by-reference
    '''
    if not mylist.has_key(newkey) :
      mylist[newkey] = []

  def setKeyIfNotExistsInt( self, mylist, newkey, initval ):
    '''
      call-by-reference
    '''
    if not mylist.has_key(newkey) :
      mylist[newkey] = initval

  def getFirstKey( self, keys ):
    '''
      returns the first date
      precondition: keys is not empty
    '''
    return keys[0]

  
  
  def normalizeToDay(self, sec):
    '''
      translate day-seconds to seconds equilvalent to YYYY-MM-DD 00:00:01
    '''
    self.macroenv.tracenv.log.debug("normalizeToDay pre : "+str(sec))
    #self.macroenv.tracenv.log.warning("normalizeToDay pre : "+datetime.datetime.fromtimestamp(sec).strftime("%Y-%m-%d %H:%M:%S")+"  "+str(sec % 86400)  )
    #r = ( ( sec - (sec % 86400) ) + 1 )
    
    dt = datetime.datetime.fromtimestamp(sec)
    return( self.datetime2seconds(datetime.datetime( int(dt.year), int(dt.month), int(dt.day), 0, 0, 1)) )

  def string2date( self, mystring ):
    '''
      a string YYYY-MM-DD is translated into the corresponding datetime
      float timestamp can be handled to
    '''
    if isinstance(mystring, float): # fallback if float
      mystring = self.getDateString(mystring)
    
    tmp = string.split( mystring, "-")
    return datetime.datetime( int(tmp[0]), int(tmp[1]), int(tmp[2]) )

  def addJsChartFiles( self ):
    '''
      add css and javascript files
    '''
    add_script( self.macroenv.tracreq, 'projectplan/js/jquery-burndown/raphael.js' )
    add_script( self.macroenv.tracreq, 'projectplan/js/jquery-burndown/raphael_002.js' )
    add_script( self.macroenv.tracreq, 'projectplan/js/jquery-burndown/burndown.js' )

  def render(self, ticketset):
    '''
      Generate HTML List
    '''
    return tag.div('base class chart renderer: no rendering')

#RenderRegister.add( SimpleRenderer, 'simplerender' )




class BurndownChart(ChartRenderer):
  '''
    check tickets not closed at the given 
  '''
  segment = ''
  segmentDefault = 'day'
  firstsegment = ''
  lastsegment = ''
  allowedSegments = ['day','week','twoweek','month','year'] # implemented
  finishStatus = ['closed','in_QA'] 
  
  def __init__(self, macroenv ):
    ChartRenderer.__init__(self, macroenv)
    # width of chart
    self.width = int(self.macroenv.macrokw.get( 'width', '800').strip())
    # height of chart
    self.height = int(self.macroenv.macrokw.get( 'height', '350').strip())
    # time segment of x-axis: days or week
    self.segment = self.macroenv.macrokw.get( 'segment', '').strip()
    if not ( self.segment in self.allowedSegments ) :
      #self.segment = self.segmentDefault # default time segment style
      raise Exception('Unknown segment configuration: %s (allowed: %s)' % (str(self.segment),self.allowedSegments))
    
    self.firstsegment = self.macroenv.macrokw.get( 'first', '').strip()
    self.lastsegment = self.macroenv.macrokw.get( 'last', '').strip()
    if self.firstsegment == '':
      self.firstsegment = None
    if self.lastsegment == '':
      self.lastsegment = None
    
    finishStatus = self.macroenv.macrokw.get( 'finishstatus', '').strip().split('|')
    if len(finishStatus) > 0 and finishStatus[0] != "":
      self.finishStatus = finishStatus
    else:
      pass # use default values
      
  def getFinishStatus( self ):
    return self.finishStatus

  def getEndOfSegment( self, changeday ):
    if self.segment == 'day':
      return(changeday)
    elif self.segment == 'week':
      dt = self.seconds2datetime(changeday)
      end = dt + datetime.timedelta( days = (7 - dt.isoweekday() - 1) ) # end of week: saturday
      #end = dt + datetime.timedelta( days = (7 - dt.weekday()) ) # end of week: sunday
      return(self.datetime2seconds(end))
    elif self.segment == 'month':
      dt = self.seconds2datetime(changeday)
      end = dt + datetime.timedelta( days = 31 ) # next month
      return(self.datetime2seconds( datetime.datetime( end.year, end.month, 1 ) - datetime.timedelta( days = 1) )) # last day of month
    elif self.segment == 'year':
      dt = self.seconds2datetime(changeday)
      end = self.datetime2seconds(  datetime.datetime( dt.year, 12, 31, 23, 59, 59 ) )
      return end
    else:
      raise Exception('Unknown segment configuration: '+str(self.segment))

  #def getSegmentString( self, changeday ):
    #if self.segment == 'day':
      #return self.getDateString(changeday)
    #if self.segment == 'week':
      #dt = self.seconds2datetime(changeday)
      #return 'week '+str(dt.isocalendar()[1])+'/'+str(dt.isocalendar()[0])
    #if self.segment == 'month':
      #dt = self.seconds2datetime(changeday)
      #return str(dt.month)+' / '+str(dt.year)
    #if self.segment == 'year':
      #dt = self.seconds2datetime(changeday)
      #return str(dt.year)

  def aggregateDates( self, changes ):
    '''
      dict (key: time) is aggregated
    '''
    newchanges = {}
    if self.segment == 'day' : # no change, as days already
      return changes
    else: # week, month
      newchanges = {}
      keys = changes.keys()
      keys.sort()
      for changeday in keys:
        endofsegment = self.getEndOfSegment(changeday)
        self.setKeyIfNotExists( newchanges, endofsegment )
        self.macroenv.tracenv.log.debug("aggregateDates: "+self.segment+": "+self.getDateString(endofsegment)+" = "+str(changes[changeday])+"  "+self.getDateString(changeday) )
        newchanges[endofsegment] = changes[changeday]
      return newchanges

  def getFirstDate( self ):
    return self.string2date( self.firstsegment )

  def getLastDate( self ):
    return self.string2date( self.lastsegment )
    
  def getBoundariesConf( self ):
    '''
      returns the macro parameters
    '''
    first = self.firstsegment
    last = self.lastsegment
    
    daydiff = datetime.timedelta(days=1)
    
    if first != None: 
      if first.lower() in self.weekdays:
        first = first.lower()
        currentday = datetime.datetime.today()
        self.macroenv.tracenv.log.debug("first weekday: "+str(currentday.weekday() ))
        while self.weekdays[currentday.weekday()].lower() != first:
          currentday = currentday - daydiff
        first = self.datetime2seconds(currentday)
        self.macroenv.tracenv.log.debug("first weekday: "+self.getDateString(first)+' param:'+str(first) )
      else:
        first = self.datetime2seconds( self.getFirstDate() )
    
    if last != None:
      if last.lower() in self.weekdays:
        last = last.lower()
        currentday = datetime.datetime.today()
        self.macroenv.tracenv.log.debug("last weekday: "+str(currentday.weekday() ))
        
        if first == last : # add one day, if e.g. "fr" to "fr"
          current = current + daydiff
        
        while self.weekdays[currentday.weekday()].lower() != last:
          currentday = currentday + daydiff
        last = self.datetime2seconds(currentday)
        self.macroenv.tracenv.log.debug("last weekday: "+self.getDateString(last)+' param:'+str(last) )
      else:
        last = self.datetime2seconds( self.getLastDate() ) 
    
    return ( first, last )
  
  def getBoundaries( self, datedict ):
    '''
      returns a tuple (firstday,lastday)
    '''
    keys = datedict.keys()
    keys.sort()
    
    nowInSeconds = self.datetime2seconds( datetime.datetime.today() )
    
    # save values in keys
    if len(keys) > 0 :
      firstdayInKeys = keys[0]
      lastdayInKeys = keys[ len(keys) - 1] 
    else:
      firstdayInKeys = self.datetime2seconds( datetime.date.today() )
      lastdayInKeys = firstdayInKeys
    
    (firstdayConf, lastdayConf) = self.getBoundariesConf()
    
    # use the marco parameter if set
    if firstdayConf != None:
      firstday = firstdayConf
    else:
      firstday = firstdayInKeys
    
    if lastdayConf != None:
      lastday = lastdayConf
    else:
      if lastdayInKeys < nowInSeconds:
        lastday = nowInSeconds
      else:
        lastday = lastdayInKeys
    
    firstday = self.normalizeToDay(firstday) # seconds of YYYY-MM-DD  HH:ii:01
    lastday = self.normalizeToDay(lastday) # seconds of YYYY-MM-DD  HH:ii:01
    
    self.macroenv.tracenv.log.debug("getBoundaries: firstday=%s (%s) lastday=%s (%s)" % (firstday,self.getDateString(firstday), lastday,self.getDateString(lastday) ) )
    
    return (firstday, lastday)

  def getLabel( self ):
    '''
      labels of the chart
    '''
    field = self.getField() 
    if field == 'status':
      return(('tickets left: ', 'tickets closed: '))
    else:
      return((''+field+': ', 'reduced by: '))
  
  def getChangeOfOpenTickets(self, oldvalue, newvalue, closeStatus):
    '''
      calculate the change of the number of open tickets based on the actions: oldvalue -> newvalue
    '''
    # decrease the number of open tickets, e.g., assigned -> closed
    if (not oldvalue in closeStatus) and (newvalue in closeStatus):
      return -1
    # increase the number of open tickets, e.g., closed -> reopened
    elif (oldvalue in closeStatus) and (not newvalue in closeStatus):
      return +1
    else:
      return 0
      
  def getTicketWeight( self, ticket, consideredField ):
    if consideredField == 'status' : # ticket status
      return 1
    else: # try to use the field given by the user
      try:
        return float(ticket.getfield(consideredField))
      except:
        return 1

  def computeInformationAboutSegment( self, ticketset, firstday, lastday ):
    '''
      returns a tupel
    '''
    fieldconf = self.getField()
    relevantChanges = {}    
    ticketCount = 0
    tickets = ticketset.getIDList()
    
    for tid in tickets :
      ticket = ticketset.getTicket(tid)
      ticketWeight = self.getTicketWeight(ticket, fieldconf) 
      
      # save the changes of each ticket to an array
      changelogOfTicket = ticketset.get_changelog(tid)
      changelogOfTicket.reverse() # initial value at last
      thisIsTheLastTime = False
      ticketIsRelevant = False
      
      # if no change was done, the ticket is still important
      if len(changelogOfTicket) == 0:
        ticketIsRelevant = True
      
      for changetime, author, field, oldvalue, newvalue, perm in changelogOfTicket: # going backwards
	changetimeSec = self.datetime2seconds(changetime) 
	changetimeDay = self.seconds2dayseconds(changetimeSec)
	dateStr = self.getDateString(changetime)
	if field == self.TICKET_STATUS_FIELD:
	  if lastday < changetimeSec:
	    # ignore
	    continue
	  elif firstday <= changetimeSec and changetimeSec <= lastday:
	    self.setKeyIfNotExistsInt( relevantChanges, dateStr, 0)
	    openTicketNumberChange = self.getChangeOfOpenTickets( oldvalue, newvalue, self.getFinishStatus() ) * ticketWeight
	    relevantChanges[dateStr] = relevantChanges[dateStr] + openTicketNumberChange
	    self.macroenv.tracenv.log.debug("ticket changes on %s (%s): #%s: ( old:%s -> new:%s ) ==> %s (%s)" % (dateStr, field, tid, oldvalue, newvalue, openTicketNumberChange,relevantChanges[dateStr])  )
	    ticketIsRelevant = True # this ticket matters
	  elif changetimeSec < firstday and thisIsTheLastTime == False: # do this only one time
	    thisIsTheLastTime = True
	    if not newvalue in self.finishStatus:
	      ticketIsRelevant = True # this ticket matters for the time period as it is not finished
      
      if ticketIsRelevant == True:
        ticketCount = ticketCount + ( 1 * ticketWeight )
    
    self.macroenv.tracenv.log.debug("ticketCount: %s" % (ticketCount,) )
    return (ticketCount, relevantChanges)
    
  def getAllRelevantDates(self, firstday, lastday):
    '''
      compute a list date strings that are relevant for the configured time period
    '''
    alldates = {}
    currentday = firstday
    while currentday <= lastday: # determine all days
      alldates[self.getDateString(currentday)] = ''
      currentday = currentday + 86400
    return alldates.keys()

  def render(self, ticketset):
    # add needed javascript and css files
    self.addJsChartFiles()
    
    if self.firstsegment == None or self.lastsegment == None:
      return self.divWarning('you have to set the time period via the macro parameters. Example: first=2012-02-03, last=2012-02-19 .')
    
    tickets = ticketset.getIDList()
    
    # stop if no tickets available
    if len(tickets) == 0:
      return self.divWarning('No tickets available.')
    
    changes = {}    
    initalvalues = {}
    creationdates = {}
    
    (firstday,lastday) = self.getBoundaries({})
    alldates = self.getAllRelevantDates(firstday, lastday)

    lastdaySecs = lastday
    firstday = self.normalizeToDay(firstday)
    lastday = self.normalizeToDay(lastday)

    (ticketCount, relevantChanges) = self.computeInformationAboutSegment( ticketset, firstday, lastday )


    # count only the tickets that are relevant within the requested time period (firstday,lastday)
    relevantTickets = ticketCount
    closedTickets = {} # change this
    openTickets = {} # change this
    changeDateStrings = relevantChanges.keys()
    changeDateStrings.sort()
    # ticketCount = 70 # DEBUG
    
    for changeDateStr in changeDateStrings: # for each day
      self.macroenv.tracenv.log.debug("changes %4s: %3s (%s)" % (changeDateStr,relevantChanges[changeDateStr], ticketCount))
      self.setKeyIfNotExistsInt( closedTickets, changeDateStr, -1*relevantChanges[changeDateStr] )
      ticketCount = ticketCount + relevantChanges[changeDateStr]  # reduce the number of open tickets
      self.setKeyIfNotExistsInt( openTickets  , changeDateStr, ticketCount)

    # generate HTML 
    holderid = "%s_%s_%d_%d" % (self.getNameOfRenderFrame(),'holder',int(time.time()*1000000),random.randint(1,1024) ) # compute unique element id
    currentday = firstday
    frame = tag.div( class_= 'invisible ppConfBurnDown', id=self.getNameOfRenderFrame()+holderid ) 
    tableData = tag.table( class_="invisible data" , border = "1", style = 'width:auto;')
    trDays = tag.tr()
    trDaysAxis = tag.tr()
    trOpenTickets = tag.tr()
    trClosedTickets = tag.tr()
    trReopenedTickets = tag.tr()
    alldates.sort()
    lastOpenTicket = relevantTickets # fallback: all tickets
    lastClosedTickets = 0
    counter = 0
    todaySecs = self.datetime2seconds( datetime.datetime.today() )
    todayStr = self.getDateString(todaySecs)
    todayid = 0
    maxValue = 0
    if lastdaySecs <= todaySecs: # if today is later then the shown time frame then mark the last column
      todayid = len(alldates)
    for currentday in alldates:
      if currentday == todayStr: # capture the column with the current date
        todayid = counter 
      counter = counter + 1
      trDays(tag.th(currentday.replace("\n"," "))) # text for info box, no line breaks here, because it is limited to 3 lines
      trDaysAxis(tag.th(currentday))
      if openTickets.has_key(currentday) :
        lastOpenTicket = openTickets[currentday]
      trOpenTickets(tag.td(lastOpenTicket))
      if closedTickets.has_key(currentday) :
        lastClosedTickets = closedTickets[currentday]
      else:
        lastClosedTickets = 0
      trClosedTickets(tag.td(lastClosedTickets))
      maxValue = max(len(str(lastClosedTickets)),len(str(lastOpenTicket)),maxValue)
      trReopenedTickets(tag.td('0'))
    
    tableData(tag.thead(trDays))
    tableData(tag.tfoot(trDaysAxis))
    tableData(tag.tbody(trOpenTickets, trClosedTickets, trReopenedTickets ))
    
    
    (label1,label2) = self.getLabel()
    
    # caculate the scale factor for the info box within the chart
    maxGlobal = max( len(str(label1))+maxValue, len(str(label2))+maxValue )
    if self.segment in ['week','twoweek']: # they use long descriptions in the info box
      maxGlobal = max(maxGlobal, 27)
    
    # configuration of renderer
    frame(tag.div( str(relevantTickets), class_ = 'maxTasks' ))
    frame(tag.div( self.width, class_ = 'width' ))
    frame(tag.div( self.height, class_ = 'height' ))
    frame(tag.div( str(maxGlobal), class_ = 'maxlength' ))
    frame(tag.div( label1, class_ = 'label1' ))
    frame(tag.div( label2, class_ = 'label2' ))
    frame(tag.div( str(todayid), class_ = 'today' )) # number of column with the current date
    frame(tag.div( holderid, class_ = 'holder' )) # where to put the chart in
    
    frame(tableData)
    outerframe = tag.div() # div as global container
    #outerframe(outer) # DEBUG
    outerframe(frame)
    outerframe(tag.div( id = holderid ), style="border-width:1px" )
    return outerframe


class BurndownChartTickets( BurndownChart ):
  '''
    default field value is the number of open/closed tickets
  '''
  def __init__(self, macroenv ):
    BurndownChart.__init__(self, macroenv)
  

