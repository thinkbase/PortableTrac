# -*- coding: utf-8 -*-

'''
  refactored version of SortedReportRenderer
  
  known bugs: table sorter does not work while using showdescription parameter
'''


import string
import datetime
import time
import os
from genshi.builder import tag
from genshi.input import HTMLParser
from genshi.core import Stream as EventStream, Markup
from genshi.template.markup import MarkupTemplate

from pprenderimpl import RenderImpl
from trac.web.chrome import add_stylesheet, add_script


class ReportRenderer(RenderImpl):
  '''
    Base Class for Renderer which enumerates a TicketSet,
    Sort them by a given Key and Output them into a HTML Table
  '''
  
  # Map resolving the row to a real name
  headermap = { 
                      'id': 'ticket', 
                      #'summary': 'Summary', 
                      #'component': 'Component' ,
                      #'status': 'Status',
                      'type': 'ticket type',
                      'time': 'created'
                  }
  # default value, overwritten by macro parameter "rows"
  fields = [ 'id', 'summary' ] 
  # all field are shown (True)
  allfields = False 
  # all fields are shown, excluding these
  allfieldsexclude = [ 'href', 'priority_value' ] 
  ascending = True
  # specific rows are extended with images (True)
  useimages = False
  usecolors = False
  
  # map resolving the sorting type (jquery.tablesorter), TODO: fix it, does not work considering buffer
  sorttype = {  
                      #'id': '{sorter: \'digit\'}' , 
                      #'buffer': '{sorter: \'digit\'}' , 
                      #'closingdiff': '{sorter: \'digit\'}' ,
                      #'assigndiff': '{sorter: \'digit\'}' 
                  }

  def __init__(self,macroenv):
    '''
      Initialize and Set Sort Key, Sort Order, Fields/Extensions to show in the Output
      and a Mapping for Field Headers.
    '''
    RenderImpl.__init__(self,macroenv)
    self.extensions = []
    self.sortkey = self.setsortkey('id') # default: id
    self.imgpath = macroenv.tracreq.href.chrome( 'projectplan', self.macroenv.PPConstant.RelDocPath );
    try:
      self.limitlines = int(self.macroenv.macrokw.get( 'limitlines', 0 ))
    except:
      self.limitlines = 0
    
    # rows configured by user
    confrows = self.macroenv.macrokw.get( 'rows', '' ).strip() # deprecated: stupid error
    confcols = self.macroenv.macrokw.get( 'cols', '' ).strip()
    if confcols != '':
      confrows = confcols
    
    if confrows.upper() == 'ALL': # show all existing fields
      self.allfields = True
    else: # show a specified set of fields
      if confrows != '' :
        self.rows = [ r.strip() for r in confrows.split('|') if str(r).strip() != "" ]
        self.fields = ['id']
        self.fields.extend(self.rows)
      else:
        self.rows = []
    
    # should images be used in the cols
    self.useimages = self.macroenv.get_bool_arg('useimages', self.useimages )
    self.usecolors = self.macroenv.get_bool_arg('usecolors', self.usecolors )
    self.setascending(True)

  def setsortkey( self, default ):
    '''
      set the standard table sort attribute
      if it is not given or it does not exists within the fields/extensions then the default value is used
      always call this method after setting self.fields and self.extensions
    '''
    self.sortkey = self.getsortkey(default)
  
  def getsortkey( self, default = 'id' ):
    sortkey = self.macroenv.macrokw.get( 'sortby', default )
    #self.macroenv.tracenv.log.debug('sortkey='+sortkey)
    if (sortkey in self.fields) or (sortkey in self.extensions) :
      pass
    else:
      sortkey = default
    return sortkey

  def setascending( self, default ):
    '''
      set the standard table sort attribute
      if it is not given or it does not exists within the fields/extensions then the default value is used
      always call this method after setting self.fields and self.extensions
    '''
    self.ascending = self.macroenv.get_bool_arg('asc', default )

  def getascending( self ):
    return(self.ascending)
  
  
  def keysortedids( self, ticketset ):
    '''
      Build an ID:Sortkey Mapping, Sort it, and Return the Sorted IDs in a List
    '''
    tdict = dict()
    sortkey = self.getsortkey()
    for tid in ticketset.getIDList():
      t = ticketset.getTicket(tid)
      if sortkey in self.fields:
        tdict[ tid ] = t.getfielddef( self.sortkey, '' )
      elif sortkey in self.extensions:
        if t.hasextension( sortkey ):
          tdict[ tid ] = t.getextension( sortkey )
        else:
          tdict[ tid ] = ''
      else:
        raise Exception( 'sortkey "%s, %s" unknown' % (sortkey,self.getsortkey() ))
    # sort
    srtkeys = [kk for (kk,vv) in sorted( tdict.iteritems(), key=lambda (k,v): (v,k))]
    # if descending, reverse the list
    if not self.getascending():
      srtkeys.reverse()
    return srtkeys

  def getcssheaderclass( self, field ):
    '''
      get css class needed for tablesorter
    '''
    sorttype = self.sorttype.get( field, '')
    sortkey = self.getsortkey()
    self.macroenv.tracenv.log.debug('sort field:'+field+' sorttype='+str(sorttype)+' self.sortkey='+sortkey )
    
    if field == sortkey:
      if self.getascending() == True:
        return 'headerSortDown sortStart '+sorttype
      else:
        return 'headerSortUp sortStart '+sorttype
    else:
      return sorttype

  # bad style, this functionality should be placed somewhere else
  def getcsscolstyle(self, field, value):
    '''
      calculates css-style information
      returns tuple (class,style)
    '''
    if (not self.useimages) and (not self.usecolors): # no images by configuration
      self.macroenv.tracenv.log.debug(field+'   no color')
      return ('', '')
    
    backgroundimage = ''
    color = ''
    cssclass = ''
    
    # choose image
    if self.useimages == True:
      backgroundimage = { # switch/case in Python style
          'status': self.macroenv.conf.get_map_val('ImageForStatus', value ),
          'priority': self.macroenv.conf.get_map_val('ImageForPriority', value ),
          'type': self.macroenv.conf.get_map_val('ImageForTicketType', value ),
        }.get( field, '' ) # fallback: empty
      if backgroundimage != '' :
        cssclass = 'ppimagecol'
        backgroundimage = ('background-image: url(%s);' % os.path.join( self.imgpath, backgroundimage ))
    
    # choose image 
    if self.usecolors == True:
      color = { # switch/case in Python style
          'status': self.macroenv.conf.get_map_val('ColorForStatus', value ),
          'priority': self.macroenv.conf.get_map_val('ColorForPriority', value ),
          'type': self.macroenv.conf.get_map_val('ColorForTicketType', value ),
        }.get( field, '' ) # fallback: empty
      if color != '' :
        color = ('background-color: %s;' % color )
    
    return (cssclass,  backgroundimage+color)


  def render(self, ticketset):
    '''
      Generate a HTML Table for the Fields/Extensions given
    '''
    # style overwritten to prevent browser rendering issues 
    #outer = tag.table( class_="listing pptickettable tablesorter pplisting" , style = 'width:auto;')
    outer = tag.table( class_="listing pptickettable tablesorter pplisting" , style = 'width:auto;')
    srtlist = self.keysortedids( ticketset )
    tablehead = tag.thead()
    inner = tag.tr()
    
    # TODO: problem: if the ticketset is empty, then the default rows will appear, 
    # solution: get the fields from somewhere else
    if self.allfields == True and len(ticketset.getIDList()) > 0:
      self.fields = []
      for f in (ticketset.getTicket(ticketset.getIDList()[0])).getfielddefs():
        if not ( f.lower() in self.allfieldsexclude ):
          self.fields.append( f )
    
    # generate HTML: Table head
    for f in self.fields:
      cssheaderclass = self.getcssheaderclass(f)
      if self.macroenv.get_bool_arg('showdescription', 'F') == True: # workaround for this parameter
        cssheaderclass = '{sorter: false}'
	
      self.macroenv.tracenv.log.debug('cssheaderclass of '+f+': '+cssheaderclass)
      if f in self.headermap:
        inner( tag.th( self.headermap[ f ] , title=f, class_ = cssheaderclass ) )
      else:
        inner( tag.th( f , class_ = cssheaderclass ) )
    for e in self.extensions:
      if e in self.headermap:
        inner( tag.th( self.headermap[ e ], title=e, class_ = self.getcssheaderclass(e) ) )
      else:
        inner( tag.th( e ), class_ = self.getcssheaderclass(e) )
    tablehead(inner)
    outer(tablehead)
   
   
    customdatefields = [ self.macroenv.conf.get( 'custom_due_assign_field' ), self.macroenv.conf.get( 'custom_due_close_field' ) ]
    def getSortableTableCell( f ):
      field = t.getfielddef( f, '' )
      cssclass,style = self.getcsscolstyle(f, field )
      if f == 'id':
        if t.getfielddef( 'status', '' )=='closed':
          cssclass ="ticket closed"
        else:
          cssclass ="ticket "
        text = tag.p(tag.a( '#'+str(t.getfielddef( f, '' )), href=t.getfielddef( 'href', '' ), class_ = cssclass ) )
      elif f == 'priority' : # special case 
        # two-digit integer representation of priority sorting (as definend in trac admin panel)
        text = tag.span(str(99-int(t.getfielddef( 'priority_value', '0' ))), class_ = 'invisible')+self.wiki2html(field)
      elif f in customdatefields : # special case: date string 
        text =  tag.span(self.getNormalizedDateStringOfSegment(field), class_='invisible')+self.wiki2html(field)
      else :
        text =  self.wiki2html(field)
      return (text,cssclass,style)
    
    
    
    
    # generate HTML: Table body
    _odd = True
    for k in srtlist:
      t = ticketset.getTicket( k )
      _odd = not _odd
      if _odd:
        inner = tag.tr( class_='odd' )
      else:
        inner = tag.tr( class_='even' )
      for f in self.fields:
        text,cssclass,style = getSortableTableCell(f)
        inner( tag.td( text, style = style, class_ = cssclass ) )
      for e in self.extensions:
        if t.hasextension( e ):
          cssclass,style = self.getcsscolstyle(e, t.getfielddef( e, '' ) )
          inner( tag.td( t.getextension( e ), style = style, class_ = cssclass  ) )
        else:
          #inner( tag.td( '0', title='no statement possible', class_ = 'ppinvisibletabletext' ) )
          inner( tag.td( '', title='no statement possible', class_ = 'ppinvisibletabletext' ) )
      outer(inner)
      
      # if macro parameter "showdescription" is set to True, then a long description is rendered into a second row spanning of all cols
      if _odd:
        inner2 = tag.tr( class_='odd' )
      else:
        inner2 = tag.tr( class_='even' )
      if self.macroenv.get_bool_arg('showdescription', 'F') == True:
        outer(inner2(tag.td(self.wiki2html(t.getfielddef( 'description', '' )), colspan=len(self.fields)+len(self.extensions) )))
      
      if self.limitlines>0:
        self.limitlines-=1;
        if self.limitlines<=0:
          break
    
    return outer


