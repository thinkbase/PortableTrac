# -*- coding: utf-8 -*-

from trac.core import *
from trac.resource import *
from genshi.builder import tag
from genshi.core import TEXT
from genshi.filters import Transformer
from genshi.input import HTML
from trac.ticket.api import ITicketManipulator
from trac.web.api import ITemplateStreamFilter, IRequestFilter #, IRequestHandler
from trac.ticket.query import *
from ppenv import PPConfiguration
from pputil import *
from trac.web.chrome import ITemplateProvider, add_stylesheet, add_script
import string
import re

class PPTicketDateTweak(Component):
  '''
    EXPERIMENTAL: adds a java script date picker to ticket view
    do not activate it if you change the default values
    currently only works with the date format MM/DD/YYYY
  '''
  implements(IRequestFilter, ITemplateStreamFilter)
  """Extension point interface for components that want to filter HTTP
    requests, before and/or after they are processed by the main handler."""
  
  
  # IRequestFilter methods
  def pre_process_request(self, req, handler):
    return handler

  def post_process_request(self, req, template, data, content_type):
    """Do any post-processing the request might need; typically adding
      values to the template `data` dictionary, or changing template or
      mime type.
      
      `data` may be update in place.
      
        Always returns a tuple of (template, data, content_type), even if
        unchanged.
        
        Note that `template`, `data`, `content_type` will be `None` if:
         - called when processing an error page
         - the default request handler did not return any result
        
        (Since Trac 0.11)
        """
    if req.path_info.startswith('/ticket/') or req.path_info.startswith('/newticket'):
      add_script( req, 'projectplan/js/ticketdatepicker.js' )
    return template, data, content_type


  # ITemplateStreamFilter methods
  def filter_stream(self, req, method, filename, stream, data):  
    '''
      add the flag that indicates the activation of the date picker javascript
    '''
    if req.path_info.startswith('/ticket/') or req.path_info.startswith('/newticket'):
      stream |= Transformer('body/div[@id="main"]').prepend(tag.div( 'activate', id='ppShowDatePicker') )
    
    return stream

