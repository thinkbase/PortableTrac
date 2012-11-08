# -*- coding: utf-8 -*-

import re

from trac.web.chrome import ITemplateProvider, add_stylesheet, add_script

class __TicketIDMatcher:
  '''
    Wrapper class for static match pattern!
    Internal use only, may be changed, deleted or replaced in future!
    Use @ticketIDsFromString instead.
  '''
  __IDMATCHPATTERN = re.compile('[0-9]+')

  @classmethod
  def idsFromString( cls, s ):
    intset = set()
    for strv in cls.__IDMATCHPATTERN.findall( s ):
      intset.add(int(strv))
    return intset

def ticketIDsFromString( s ):
  '''
    get ticket id's from string
  '''
  return __TicketIDMatcher.idsFromString( s )

def addExternFiles(req):
  '''
    add javascript and style files
  '''
  # include jquery tooltips
  add_script( req, 'projectplan/js/jquery-tooltip/lib/jquery.dimensions.js' )
  add_script( req, 'projectplan/js/jquery-tooltip/jquery.tooltip.js' )
  add_stylesheet( req, 'projectplan/css/projectplan.css' )
  
  # include jquery tablesorter
  # TODO: now included in projectplan.js to prevent errors
  # add_stylesheet( req, 'projectplan/js/jquery-tablesorter/jquery.tablesorter.min.js'); # production
  #add_stylesheet( req, 'projectplan/js/jquery-tablesorter/jquery.tablesorter.js'); # debug

  # css: jquery tooltips
  add_stylesheet( req, 'projectplan/js/jquery-tooltip/jquery.tooltip.css' )

  # PP css and js
  add_script( req, 'projectplan/js/projectplan.js' )

 
def isNumber( string ) :
  '''
    checks if the given string is a number
  '''
  try:
    stripped = str(int(string))
    return True
  except:
    return False


def htmlspecialchars(text):
  '''
    replace special characters (like in PHP)
  '''
  text = text.replace('&', '&amp;')
  text = text.replace('"', '&quot;')
  text = text.replace('<', '&lt;')
  text = text.replace('>', '&gt;')
  text = text.replace("'", '&#039;')
  return text
