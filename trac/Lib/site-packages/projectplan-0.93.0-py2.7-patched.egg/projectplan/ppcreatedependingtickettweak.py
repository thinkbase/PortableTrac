# -*- coding: utf-8 -*-

from trac.core import *
from trac.resource import *
from genshi.builder import tag
from genshi.core import TEXT
from genshi.filters import Transformer
from genshi.input import HTML
from trac.ticket.api import ITicketManipulator
from trac.web.api import IRequestFilter
from trac.ticket.query import *
from ppenv import PPConfiguration
from pputil import *
from trac.web.chrome import add_script
import string
import re

class PPCreateDependingTicketTweak(Component):
  '''
    EXPERIMENTAL: add a button allowing to create a new depending ticket
    functionality is implemented in javascript (dependingticket.js)
  '''
  implements(IRequestFilter)
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
      add_script( req, 'projectplan/js/dependingticket.js' )
    return template, data, content_type

