# -*- coding: utf-8 -*-

'''
  ALPHA
  TODO: generated HTML needs to be optimized
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

class GroupStats(RenderImpl):
  
  order = []
  
  def __init__(self,macroenv):
    self.FRAME_LABEL = 'Ticket Statistics'
    RenderImpl.__init__(self,macroenv)
    self.macroenv = macroenv
    
    # defines the order of the ticket status
    order = self.macroenv.macrokw.get('order')
    if order == None:
      self.orderOrg = ['*'] # everything is allowed
    else:
      self.orderOrg = order.split(';')

  def render(self, ticketset):
    '''
      Generate HTML List
    '''
    return tag.div('base class group stats: no rendering')

  def setKeyIfNotExists( self, mylist, newkey ):
    '''
      call-by-reference
      TODO: move to tools
    '''
    if not mylist.has_key(newkey) :
      mylist[newkey] = []

  def setKeyIfNotExistsInt( self, mylist, newkey, initval ):
    '''
      call-by-reference
      TODO: move to tools
    '''
    if not mylist.has_key(newkey) :
      mylist[newkey] = initval

  def hex2int(self, n):
    """
      Convert a hex number to decimal
      TODO: move to tools
    """
    hex2dec = {'0':0, '1':1, '2':2, '3':3,'4':4, '5':5, '6':6, '7':7,'8':8, '9':9, 'A':10, 'B':11, 'C':12, 'D':13, 'E':14, 'F':15 }
    return int("%s" % ((hex2dec[n[0]] * 16) + (hex2dec[n[1]]),))
    
  def computeDarkerColor( self, colorAsHex ):
    """
      Create a darker color
      TODO: move to tools
    """
    downGradeFactor = 0.75
    c1 = int(round(self.hex2int( colorAsHex[1]+colorAsHex[2] ) * downGradeFactor))
    c2 = int(round(self.hex2int( colorAsHex[3]+colorAsHex[4] ) * downGradeFactor))
    c3 = int(round(self.hex2int( colorAsHex[5]+colorAsHex[6] ) * downGradeFactor))
    return "rgb(%s,%s,%s)" % (c1,c2,c3)

  def getTicketGrouping( self, ticketset ):
    tickets = ticketset.getIDList()
    ticketgrouping = {}
    count = 0
    for tid in tickets:
      status = ticketset.getTicket(tid).getfield('status')
      if self.isAllowedStatus(status):
        count += 1
        summary = ticketset.getTicket(tid).getfield('summary')
        owner = ticketset.getTicket(tid).getfield('owner')
        if not ticketgrouping.has_key(status):
          ticketgrouping[status] = {}
        ticketgrouping[status][tid] = "%s (%s)" % (summary,owner)
      
    return (count,ticketgrouping)
    
  def getDimensions( self ):
    '''
      get width and height; default: (800,30)
    '''
    width = int(self.macroenv.macrokw.get( 'width', '800').strip())
    height = int(self.macroenv.macrokw.get( 'height', '30').strip())
    return (width,height)

  def isAllowedStatus( self, statuskey ):
    '''
      decides whether a ticket status has to be shown or not
    '''
    if (self.orderOrg == None) or (statuskey in self.orderOrg) or ('*' in self.orderOrg):
      return True
    else:
      return False

  def getOrderedStatusKeys( self, order, statuskeys):
    # get all status that were not demanded explicitly by the user via configuration ()
    orderedStatusKeysUnwanted = []
    for status in statuskeys:
      if not (status in order):
        orderedStatusKeysUnwanted.append(status)
    
    # create the list of ticket status demanded by the user via configuration, add unwanted to where a * is written
    orderedStatusKeys = []
    for status in order:
      if status in statuskeys:
        orderedStatusKeys.append(status)
      elif status == '*':
        for s in orderedStatusKeysUnwanted:
          orderedStatusKeys.append(s)

    return orderedStatusKeys



class GroupStatsBar(GroupStats):
  
  def __init__(self,macroenv):
    GroupStats.__init__(self,macroenv)

  def getCSSgradient( self, color ):
    darkerColor = self.computeDarkerColor(color)
    percentTop = '33%'
    percentBottom = '80%'
    return '''
      background-image: -webkit-linear-gradient(top, %s %s, %s %s);
      background-image:    -moz-linear-gradient(top, %s %s, %s %s);
      background-image:     -ms-linear-gradient(top, %s %s, %s %s);
      background-image:      -o-linear-gradient(top, %s %s, %s %s);
    ''' % (color,percentTop,darkerColor,percentBottom,color,percentTop,darkerColor,percentBottom,color,percentTop,darkerColor,percentBottom,color,percentTop,darkerColor,percentBottom)

  def render(self, ticketset):
    '''
      Generate HTML List
    '''
    (counttickets,ticketgrouping) = self.getTicketGrouping( ticketset )
    
    if counttickets == 0:
      return self.divWarning('No tickets available.')
   
    maxTicketsToShow = 20
    maxWidth = 400
    statuskeys = ticketgrouping.keys()
    (width,height) = self.getDimensions()
    
    framewrapper = tag.div(style="width:%spx;" % (width+10+(2*len(statuskeys)),) ) # ensures the width if the browser window is to small
    framebar = tag.div(class_="clearfix",style="height:%spx; background-color: #333; box-shadow: 4px 4px 4px #999; display: inline-block; white-space:nowrap; border: 1px solid #333; float: left;" % (height,) )
    js = tag.script()
    framebox = tag.div()
    currentPosition = 0 # offset
    myId = self.getStrongKey()
    orderedStatusKeys = self.getOrderedStatusKeys(self.orderOrg, statuskeys)
    
    for statuskey in orderedStatusKeys :
      groupingCount = len(ticketgrouping[statuskey])
      groupingPercent = int(round(float(groupingCount) / float(counttickets) * 100)) 
      groupingWidth = int(round(float(groupingCount) / float(counttickets) * width ))
      groupingColor = self.macroenv.conf.get_map_val('ColorForStatus', statuskey )

      barId = myId+'_bar_'+statuskey
      boxId = myId+'_box_'+statuskey
      
      statusTicketsWidth = max(groupingWidth,maxWidth)-10
      statusTickets = tag.div(id=boxId, style='width:%spx; border:1px solid %s;display:none;position:absolute;left:%spx;background-color:#FFF;padding:0.5ex;margin:0.5ex;box-shadow:4px 4px 4px #AAA;' % (statusTicketsWidth,groupingColor,currentPosition))
      ticketids = ticketgrouping[statuskey].keys()
      ticketids.sort(reverse=True)
      ticketTable = tag.table()
      for tid in ticketids[0:maxTicketsToShow]:
        ticketTable(tag.tr(tag.td(self.createTicketLink(ticketset.getTicket(tid))), tag.td(ticketgrouping[statuskey][tid], style="max-width:%spx"%(min(max(maxWidth,groupingWidth),width),)) ))
      # show the number of left out tickets
      if len(ticketids) > maxTicketsToShow :
        ticketTable(tag.tr(tag.td('...'),tag.td('%s more tickets' % (len(ticketids)-maxTicketsToShow,))))
      
      if groupingCount==1:
        ticketString = 'ticket'
      else:
        ticketString = 'tickets'

      statusTickets(tag.div(tag.div('%s %s: %s' % (groupingCount,ticketString,statuskey),style="float:left;font-weight:bold;"),tag.div(tag.a('X',href="javascript: return false;"),id="%s%s" % (boxId,"close"),style="float:right",class_="ppinsetshadow"),class_="clearFix"),ticketTable)

      framebar( tag.div( '', id=barId, style="float:left;border:1px solid #333;width:%spx; height:%spx; %s;" % (groupingWidth,height,self.getCSSgradient(groupingColor)) ) )
      framebox( statusTickets, style="position:absolute;" )
      # if clicked, show permanently; until clicked again; ppStore stores the current click state
      js('''$("#%s").mouseover(function() {
	  $("#%s").slideDown(200, function() {});  
	  });''' % (barId,boxId))
      js('''$("#%s").mouseout(function() { 
	  if(ppStore["%s"] == 0 || isNaN(ppStore["%s"])){ $("#%s").slideUp(400, function() {});  } 
	  }); ''' % (barId,barId,barId,boxId))
      js('''$("#%s").mouseup(function() { 
	  if ( isNaN(ppStore["%s"]) ) { ppStore["%s"]=0; }
	  ppStore["%s"] = (ppStore["%s"]+1) %% 2
	  if( ppStore["%s"] ==  1 ){ $("#%s").slideDown(100, function() {});  }
	  else { $("#%s").slideUp(100, function() {});  }
	  });''' % (barId,barId,barId,barId,barId,barId,boxId,boxId))
      js('''$("#%sclose").click(function() {
	  $("#%s").slideUp(100, function() {});  
	  });''' % (boxId,boxId))
      #js('$("#%s").mouseenter().mouseleave(function() {$("#%s").hide();  });' % (boxId,boxId))
      
      currentPosition += groupingWidth + 2 # offset is 2px
     
    return tag.div(framewrapper(framebar),tag.div(style="clear:both;"),framebox,js)

