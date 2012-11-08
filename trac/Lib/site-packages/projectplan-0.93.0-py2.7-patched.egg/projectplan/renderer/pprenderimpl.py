# -*- coding: utf-8 -*-

import re
import os
from datetime import *
import time
import random

from genshi.builder import tag
from trac.wiki.formatter import wiki_to_html


class RenderImpl():
  '''
    Renderer implementation baseclass
  '''
  FRAME_LABEL = 'Project Plan'

  def __init__(self,macroenv):
    '''
      Initialize
    '''
    self.macroenv = macroenv
  
  def getTitle(self):
    if self.macroenv.macrokw.get('title') != None:# title of the visualization
      #self.macroenv.tracenv.log.debug('title=%s' % (self.macroenv.macrokw.get('title'),))
      return self.macroenv.macrokw.get('title')
    else:
      return None

  
  def getHeadline( self ):
    '''
      overwrite the method 
      TODO: make abstract
    '''
    title = self.getTitle()
    if title != None:
      return('%s' % (title,))
    else:
      return('%s' % (self.FRAME_LABEL,))
  
  def log_warn( self, message ):
    '''
      shortcut: warn logging
    '''
    self.macroenv.tracenv.log.warn(message)
  
  def log_debug( self, message ):
    '''
      shortcut: warn logging
    '''
    self.macroenv.tracenv.log.debug(message)
  
  def getDateFormat( self ):
    return(self.macroenv.conf.get( 'ticketclosedf' ))
  
  def parseTimeSegment( self, timestr ):
    '''
      check for alias names in time strings, like TODAY+1
      currently only days are checked
    '''
    pat = re.compile(r'today\s*(\+|-)\s*(\d+)')
    if timestr.lower().startswith('today'): # today string
      today = date.today()
      
      matchs = pat.search(timestr)
      if matchs == None: # no calculation
        newtime = today
      else: # shift of time (by days)
        groups = matchs.groups()
        
        if groups[0] == '+':
          self.macroenv.tracenv.log.warn('parseTimeSegment ('+timestr+'): + '+repr(groups)+' '+groups[1])
          newtime = today + timedelta(days=int(groups[1]))
        else: # groups[0] == '-'
          self.macroenv.tracenv.log.warn('parseTimeSegment ('+timestr+'): - '+repr(groups)+' '+groups[1])
          newtime = today - timedelta(days=int(groups[1]))
      
      # export time to needed dateformat
      dateformat = self.getDateFormat();
      day = str(newtime.day).rjust(2, '0')
      month = str(newtime.month).rjust(2, '0')
      year = str(newtime.year).rjust(4, '0')
      if dateformat == 'MM/DD/YYYY':
        return ('%2s/%2s/%4s' % (month,day,year  ) )
      elif dateformat == 'DD/MM/YYYY':
        return ('%2s/%2s/%4s' % (day, month, year ) )
      elif dateformat == 'DD-MM-YYYY':
        return ('%2s-%2s-%4s' % (day, month, year ) )
      elif dateformat == 'YYYY-MM-DD':
        return ('%4s-%2s-%2s' % (day, month, year ) )
      else: # dateformat == 'YYYY-MM-DD':
        return ('%4s-%2s-%2s' % (day, month, year ) )
      
    else: # change nothing
      return timestr

  def getDateOfSegment( self, timestr ):
    try:
      dateformat = self.getDateFormat();
      if dateformat == 'MM/DD/YYYY':
        day = timestr[3:5]
        month = timestr[0:2]
        year = timestr[6:10]
      elif dateformat == 'DD/MM/YYYY':
        day = timestr[0:2]
        month = timestr[3:5]
        year = timestr[6:10]
      elif dateformat == 'DD-MM-YYYY':
        day = timestr[0:2]
        month = timestr[3:5]
        year = timestr[6:10]
      elif dateformat == 'YYYY-MM-DD':
        day = timestr[8:10]
        month = timestr[5:7]
        year = timestr[0:4]
      else: # dateformat == 'YYYY-MM-DD':
        day = timestr[8:10]
        month = timestr[5:7]
        year = timestr[0:4]
      self.macroenv.tracenv.log.debug('getDateOfSegment: year=%s,month=%s,day=%s' % (year,month,day))
      return(date(int(year),int(month),int(day)))
    except Exception,e:
      self.macroenv.tracenv.log.warn('getDateOfSegment: '+str(e)+' '+dateformat+' '+timestr)
      return None

  def getNormalizedDateStringOfSegment( self, timestr ):
    return self.getNormalizedDateStringOfDate(self.getDateOfSegment(timestr))
  
  def getNormalizedDateStringOfDate( self, mydate):
    if mydate == None:
      return '0000-00-00'
    else:
      return mydate.strftime('%Y-%m-%d')

  def getNormalizedDateTimeStringOfDate( self, mydatetime):
    if mydatetime == None:
      return '0000-00-00 00:00:00'
    else:
      return mydatetime.strftime('%Y-%m-%d %H:%M:%S')

  def createTicketLink(self, ticket):
    '''
      create a link to a ticket
    '''
    tid = ticket.getfield('id')
    status = ticket.getfield('status')
    priority = ticket.getfield('priority')
    white = '#FFFFFF' # fallback color
    
    cssclass = 'ticket ticket_inner'
    if status == 'closed':
      cssclass += ' closed'
    elif status == 'in_QA': # enterprise workflow
      cssclass += ' in_QA'
    
    cssclassouter = ''
    style = ''
    if self.macroenv.get_bool_arg('useimages', False ):
      cssclassouter += 'ppuseimages '
      img = os.path.join( self.macroenv.tracreq.href.chrome( 'projectplan', self.macroenv.PPConstant.RelDocPath ), self.macroenv.conf.get_map_val('ImageForStatus', status) )
      #self.macroenv.tracenv.log.debug('ppuseimages: '+repr(img)+' '+repr(status) )
      style += 'background-image:url('+img+');'
    if self.macroenv.get_bool_arg('usecolors', False ):
      cssclassouter += 'ppusecolors '
      style += 'background-color: '+self.macroenv.conf.get_map_defaults('ColorForPriority', priority, white)
    return tag.span( tag.span( tag.a('#'+str(tid), href=self.macroenv.tracenv.href.ticket(tid), class_ = cssclass, style = style ), class_ = cssclassouter ), class_ = 'ppticket' )
  
  def createGoogleChartFromDict( self, colorschema, mydict, title='', width=170, height=50 ):
    
    #Example: http://chart.googleapis.com/chart?chf=bg,s,FFFFFF00&cht=p&chd=t:1,4,1,1&chs=200x100&chdl=January|February|March|April
    googlecharturl = 'chart.googleapis.com/chart'
    
    keys = []
    values = []
    colors = []
    
    for key in mydict :
      keys.append('%s (%s)' % (key,str(mydict[key]) ))
      values.append(str(mydict[key]))
      colors.append(self.macroenv.conf.get_map_val(colorschema, key)[1:] ) # remove #
    
    # convient issue: remove color if no chart element is contained 
    if len(colors) == 0:
      colors.append('FFFFFF00') # transparent
    
    # nr = random.randrange(0, 9) # randomize server
    
    if title != '' :
      title = '&chtt=%s&chts=333333,10.5' % (title,)
    
    return('https://%s?chf=bg,s,FFFFFF00&cht=p3&chd=t:%s&chs=%sx%s&chma=|0,%s&chdl=%s&chco=%s%s' % (googlecharturl,  ','.join(values),  width,  height, height, '|'.join(keys), ','.join(colors), title) )
  
  def wiki2html( self, myinput ):
    '''
      transform wiki markup to HTML code
    '''
    if type(myinput) == datetime.date:
      mystring = self.getNormalizedDateStringOfDate(myinput)
    elif type(myinput) == datetime:
      mystring = self.getNormalizedDateTimeStringOfDate(myinput)
    else:
      mystring = myinput
    
    return wiki_to_html(mystring, self.macroenv.tracenv, self.macroenv.tracreq)

  def divWarning(self, mystr):
    '''
      computes a div with a warning markup
    '''
    return tag.div( mystr, class_='ppwarning' )

  def getStrongKey( self ):
    '''
      creates a unique element id 
    '''
    return "%s_%d_%d" % ('ppelement',int(time.time()*1000000),random.randint(1,1000000) ) 
    
  def render(self, ticketset):
    '''
      Generate Output and Return XML/HTML Code/Tags suited for Genshi
    '''
    pass
    
    
