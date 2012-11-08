# -*- coding: utf-8 -*-

import re
import math
import os

from genshi.builder import tag
from genshi.input import HTMLParser
from genshi.core import Stream as EventStream, Markup
from genshi.template.markup import MarkupTemplate
from pptickets import *
from pputil import *
from ppenv import PPConstant
import ppenv

from dotrender import GVCMapXGen
from gvproto import GVRenderProto
from renderer import *

import trac.ticket.model



#class RenderImpl():
  #'''
    #Renderer implementation baseclass
  #'''

  #def __init__(self,macroenv):
    #'''
      #Initialize
    #'''
    #self.macroenv = macroenv
    
  #def log_warn( self, message ):
    #'''
      #shortcut: warn logging
    #'''
    #self.macroenv.tracenv.log.warn(message)

  #def render(self, ticketset):
    #'''
      #Generate Output and Return XML/HTML Code/Tags suited for Genshi
    #'''
    #pass

class RenderRegister(object):
  '''
    RenderRegister
  '''

  __r = {}

  @classmethod
  def add(cls,registrantcls,registername):
    '''
      Add a RenderImpl Class:Name pair into the Render Register
    '''
    cls.__r[ registername ] = registrantcls

  @classmethod
  def keys(cls):
    '''
      Return the current Names
    '''
    return cls.__r.keys()

  @classmethod
  def get(cls,registername):
    '''
      Return the Class for the given Name
    '''
    return cls.__r[ registername ]

class SimpleRenderer(RenderImpl):
  '''
    Simple Renderer
      this renderer simply generates a List of tickets:
      <ul>
        <li>id:summary</li>
        ...
      </ul>

  '''
  def render(self, ticketset):
    '''
      Generate HTML List
    '''
    return tag.ul([tag.li(str(ticketset.getTicket(t).getfield('id'))+':'+
                          ticketset.getTicket(t).getfield('summary')) for t in ticketset.getIDList()])

RenderRegister.add( SimpleRenderer, 'simplerender' )

class SortedReportRenderer(RenderImpl):
  '''
    Base Class for Renderer which enumerate a TicketSet,
    Sort them by a given Key and Output them into a HTML Table
    @deprecated
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
    self.imgpath = macroenv.tracreq.href.chrome( 'projectplan', PPConstant.RelDocPath );
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
    
    # generate HTML: Table body
    _odd = True
    for k in srtlist:
      t = ticketset.getTicket( k )
      if _odd:
        inner = tag.tr( class_='odd' )
      else:
        inner = tag.tr( class_='even' )
      _odd = not _odd
      for f in self.fields:
        if f == 'id':
          if t.getfielddef( 'status', '' )=='closed':
            cssclass ="ticket closed"
          else:
            cssclass ="ticket "
          inner( tag.td( tag.a( '#'+str(t.getfielddef( f, '' )), href=t.getfielddef( 'href', '' ), class_ = cssclass ) ) )
        else:
          cssclass,style = self.getcsscolstyle(f, t.getfielddef( f, '' ) )
          if f == 'priority' : # special case 
            # two-digit integer representation of priority sorting (as definend in trac admin panel)
            text = tag.span(str(99-int(t.getfielddef( 'priority_value', '0' ))), class_ = 'invisible')+' '+t.getfielddef( f, '' ) 
          else :
            text = t.getfielddef( f, '' )
          inner( tag.td( text, style = style, class_ = cssclass ) )
      for e in self.extensions:
        if t.hasextension( e ):
          cssclass,style = self.getcsscolstyle(e, t.getfielddef( e, '' ) )
          inner( tag.td( t.getextension( e ), style = style, class_ = cssclass  ) )
        else:
          #inner( tag.td( '0', title='no statement possible', class_ = 'ppinvisibletabletext' ) )
          inner( tag.td( '', title='no statement possible', class_ = 'ppinvisibletabletext' ) )
      outer(inner)
      if self.limitlines>0:
        self.limitlines-=1;
        if self.limitlines<=0:
          break
    
    return outer

#RenderRegister.add( SortedReportRenderer, 'report' )
RenderRegister.add( ReportRenderer, 'report' )



class SortedBufferReportRenderer(SortedReportRenderer):
  '''
    Sorted Report Renderer which Sorts per Buffer Extension
    (needs criticalpath_simple extension)
  '''

  def __init__(self,macroenv):
    '''
      Initialize Fields/Extensions to be shown
    '''
    SortedReportRenderer.__init__(self,macroenv)
    #self.fields = [ 'id', 'summary' ] # has to be performed before super constructor
    self.extensions = [ 'buffer' ]
    self.headermap.update({ 'buffer': 'Buffer in days' })
    self.setsortkey('buffer')
    self.setascending(True)

  def render(self,ticketset):
    '''
      Execute Extention and use the inherited Render method for Rendering
    '''
    ticketset.needExtension( 'duetimediffs' )
    ticketset.needExtension( 'criticalpath_simple' )
    return SortedReportRenderer.render( self, ticketset )

RenderRegister.add( SortedBufferReportRenderer, 'report_buffer' )

class SortedClosingDelayReportRenderer(SortedReportRenderer):
  '''
    Sorted Report Renderer which Sorts per Closing Delay Extension
    (needs duetimediffs extension)
  '''

  def __init__(self,macroenv):
    '''
      Initialize Fields/Extensions to be shown
    '''
    SortedReportRenderer.__init__(self,macroenv)
    #self.fields = [ 'id', 'summary' ] # has to be performed before super constructor
    self.extensions = [ 'closingdiff' ]
    self.headermap.update({ 'closingdiff': 'Closing delay in days' })
    self.setsortkey('closingdiff')
    self.setascending(False)

  def render(self,ticketset):
    '''
      Execute Extention and use the inherited Render method for Rendering
    '''
    ticketset.needExtension( 'duetimediffs' )
    return SortedReportRenderer.render( self, ticketset )

RenderRegister.add( SortedClosingDelayReportRenderer, 'report_closing_delay' )

class SortedAssignDelayReportRenderer(SortedReportRenderer):
  '''
    Sorted Report Renderer which Sorts per Assignment Delay Extension
    (needs duetimediffs extension)
  '''

  def __init__(self,macroenv):
    '''
      Initialize Fields/Extensions to be shown
    '''
    SortedReportRenderer.__init__(self,macroenv)
    #self.fields = [ 'id', 'summary' ] # has to be performed before super constructor
    self.extensions = [ 'assigndiff' ]
    self.headermap.update({ 'assigndiff': 'Assignment delay in days' })
    self.setsortkey('assigndiff')
    self.setascending(False)

  def render(self,ticketset):
    '''
      Execute Extention and use the inherited Render method for Rendering
    '''
    ticketset.needExtension( 'duetimediffs' )
    return SortedReportRenderer.render( self, ticketset )

RenderRegister.add( SortedAssignDelayReportRenderer, 'report_assign_delay' )




class GVRenderer(RenderImpl):
  '''
    Graphviz Renderer
      extended renderer which uses graphviz (dot for DAGs [directed acyclic graphs]) as generator/preprocessor
      for ticket positioning

      currently this is done in 2 steps:
        1. generate the resulting picture for the ticket dependency DAG and the client-side map (cmapx)
        2. reparse the client-side map and generate more powerfull html code
        note: the second step is needed to transform the produced html
              since graphviz doesn't realy understand HTML (strict/transient/whatever) but
              a small subset consisting of table/td/tr and some stuff for fontsize/color
  '''

  # Rectangle Field order for HTML Client Map Areas
  RECT_LEFT = 0
  RECT_TOP = 1
  RECT_RIGHT = 2
  RECT_BOTTOM = 3
  
  DEFAULT_GVRENDER_MACROID = '2' # standard macro

  # Dummy Frame Address and Label for the Toplevel Cluster
  # (all other Nodes and Cluster Frames are in this rect) Area
  FRAME_ADDR = "http://dummy.invalid"
  FRAME_LABEL = "Project Plan"
  
  # if true the cache will not be used
  ppforcereload = False

  def __init__(self,macroenv):
    '''
      Initialize
    '''
    RenderImpl.__init__(self,macroenv)
    self.cmapxgen = None
    self.imgpath = ppenv.PPImageSelOption.absbasepath()
    
    #macroenv.tracenv.log.warning("force reload: ppforcereload=%s " % repr(macroenv.get_args('ppforcereload') ) )
    if macroenv.get_args('ppforcereload') == '1' :
      self.ppforcereload = True
    
    # TODO: move this to the renderer implementation
    if macroenv.macrokw.get('title') != None:# title of the visualization
      #macroenv.tracenv.log.debug('title=%s' % (macroenv.macrokw.get('title'),))
      self.FRAME_LABEL = macroenv.macrokw.get('title')
    
    if macroenv.macroid.upper() == 'NONE' or macroenv.macroid == None or macroenv.macroid == '':
      macroenv.macroid = self.DEFAULT_GVRENDER_MACROID
    
    try:
      milestone_style = macroenv.macrokw.get('milestones').upper()
    except:
      milestone_style = 'ON'
    
    if str(macroenv.macroid) == '3' or ( milestone_style == 'OFF' ) :  # first: deprecated configuration
      macroenv.tracenv.log.warning('GVRenderer: milestone_style -> overwrite _writeMilestoneClusterHeader _writeMilestoneClusterFooter')
      self._writeMilestoneClusterHeader = dummy
      self._writeMilestoneClusterFooter = dummy
    
    try:
      version_style = macroenv.macrokw.get('versions').upper()
    except:
      version_style = 'ON'
    
    if ( version_style == 'OFF' ) :  # show no milestone box
      macroenv.tracenv.log.warning('GVRenderer: version_style -> overwrite _writeVersionClusterHeader _writeVersionClusterFooter')
      self._writeVersionClusterHeader = dummy
      self._writeVersionClusterFooter = dummy

  def isForceReload(self):
    return self.ppforcereload

  def _writeVersionClusterHeader( self, vstring, vnum, vhref=None, vtitle=None ):
    '''
      Write a Version Cluster Header (GV subgraph and attributes)
    '''
    self.cmapxgen += 'subgraph "clusterVersion_'+str(vnum)+'" { '
    if vhref!=None:
      self.cmapxgen += 'URL="?version?%s";' % str(vhref)
    else:
      self.cmapxgen += 'URL="?version?'+self.macroenv.tracreq.href('query')+'?version='+vstring+'"; '
    self.cmapxgen += 'style="filled"; '
    self.cmapxgen += 'fontsize="12"; '
    self.cmapxgen += 'fillcolor="'+self.macroenv.conf.get('version_fillcolor')+'"; '
    self.cmapxgen += 'fontcolor="'+self.macroenv.conf.get('version_fontcolor')+'"; '
    self.cmapxgen += 'color="'+self.macroenv.conf.get('version_color')+'"; '
    if vtitle!=None:
      myversion =htmlspecialchars(vtitle)
    else:
      myversion = 'Version: '+htmlspecialchars(vstring)
    # TODO: label should be better interpreted while parsing the html map
    if str(self.macroenv.macroid) in ['2', '3']: # standard rendering
      self.cmapxgen += 'label=<%s> ' % myversion
    elif str(self.macroenv.macroid) == '1' : # hierarchical rendering including closing image
      self.cmapxgen += 'label=<<TABLE BORDER="0" CELLPADDING="0" TITLE="close this version"><TR><TD>'
      self.cmapxgen += '<IMG SRC="'+os.path.join( self.imgpath, 'crystal_project/16x16/plusminus/viewmag-.png')+'"></IMG>'
      self.cmapxgen += '</TD><TD>'+myversion+'</TD></TR></TABLE>>; '+"\n"

  def _writeVersionClusterFooter( self ):
    '''
      closes the version cluster 
    '''
    self.cmapxgen += " } \n";
 
  def _writeMilestoneClusterHeader( self, mstring, mnum, mhref=None, mtitle=None ):
    '''
      Write a Milestone Cluster Header (GV subgraph and attributes)
    '''
    self.cmapxgen += 'subgraph "clusterCMilestone_'+str(mnum)+'" { '
    if mhref!=None:
      self.cmapxgen += 'URL="?milestone?%s";' % str(mhref)
    else:
      self.cmapxgen += 'URL="?milestone?'+self.macroenv.tracreq.href('query')+'?milestone='+mstring+'"; '
    self.cmapxgen += 'style="filled"; '
    self.cmapxgen += 'fontsize="12"; '
    self.cmapxgen += 'fillcolor="'+self.macroenv.conf.get('milestone_fillcolor')+'"; '
    self.cmapxgen += 'fontcolor="'+self.macroenv.conf.get('milestone_fontcolor')+'"; '
    self.cmapxgen += 'color="'+self.macroenv.conf.get('milestone_color')+'"; '
    if mtitle!=None:
      mylabel = htmlspecialchars(mtitle)
    else:
      mylabel = 'Milestone: '+ htmlspecialchars(mstring)
    # TODO: label should be better interpreted while parsing the html map
    if str(self.macroenv.macroid) in ['2', '3'] : # standard rendering
      self.cmapxgen += 'label=<%s> ' % mylabel
    elif str(self.macroenv.macroid) == '1' : # hierarchical rendering including closing image
      self.cmapxgen += 'label=<<TABLE BORDER="0" CELLPADDING="0"><TR><TD>'
      self.cmapxgen += '<IMG SRC="'+os.path.join( self.imgpath, 'crystal_project/16x16/plusminus/viewmag-.png')+'"></IMG>'
      self.cmapxgen += '</TD><TD>'+mylabel+'</TD></TR></TABLE>>; '+"\n"

  def _writeMilestoneClusterFooter( self ):
    '''
      closes the milestone cluster 
    '''
    self.cmapxgen += " } \n";

  def _writeEnumLegendCluster( self, name, enumerator_cls, colconfkey=None, imageconfkey=None ):
    '''
      Write a Legend Cluster for a given enumeration and colcor/image keys, f.e. priority and status
    '''
    if ( enumerator_cls == None ) or ( ( colconfkey==None ) and (imageconfkey==None) ):
      raise Exception( "Can't generate Legend for %s" % name )
    enumkeys = [ e.name for e in enumerator_cls.select( self.macroenv.tracenv ) ]
    self.cmapxgen += 'subgraph cluster'+name+'Legend { label="'+name+' Legend"; fontcolor="black"; fontsize="10"; color="grey"; fillcolor="white";  '
    self.cmapxgen += name+'Legend[ shape=plaintext, label=<<TABLE BORDER="0" CELLPADDING="1" CELLSPACING="3">'
    c = 0
    for k in enumkeys:
      c = c+1
      if colconfkey!=None:
        v = self.macroenv.conf.get_map_val( colconfkey, k )
      else:
        v = '#FFFFFF'
      if imageconfkey!=None:
        import os.path
        from ppenv import PPImageSelOption
        nodelabel='<TD COLOR="%s">%s</TD><TD BGCOLOR="%s"><IMG SRC="%s"></IMG></TD>' % (
          v, k, v, os.path.join( PPImageSelOption.absbasepath(), self.macroenv.conf.get_map_val( imageconfkey, k ) ) )
      else:
        nodelabel = '<TD>"%s"</TD>' % k
      #self.cmapxgen += name+'Legend_'+str(c)+' [ shape=rect, style=filled, label=%s, fillcolor="%s" ]; ' %( nodelabel, v )
      self.cmapxgen += '<TR>'+nodelabel+'</TR>'
    #for n in range( 1, c ):
      #self.cmapxgen += name+'Legend_'+str(n)+' -> '+name+'Legend_'+str(n+1)+' [ arrowhead="none", weight=10000 ]; ' #style="invisible", 
    self.cmapxgen += '</TABLE>>]' # end of node
    self.cmapxgen += '}' #end of subgraph

  def _genhierarch( self, ticketset ):
    '''
      generate a hierarchical map: map[versions][milestones][ticketobjects], which
      can be simply iterated, for generating a hierarchical Cluster/Node description.
    '''
    # trival hierarchical subclustering (version->milestone)
    hierarch_dict = dict()
    for t in ticketset.getIDList():
      ppt = ticketset.getTicket(t)
      ver = ppt.getfielddef( 'version', '' )
      if ver not in hierarch_dict:
        hierarch_dict[ ver ] = dict()
      ms = ppt.getfielddef( 'milestone', '' )
      if ms in hierarch_dict[ ver ]:
        hierarch_dict[ ver ][ ms ].append( ppt )
      else:
        hierarch_dict[ ver ].update( { ms: [ ppt ] } )
    return hierarch_dict

  def _writehierarch( self, hierarch_dict ):
    '''
      generate the given hierarchie - generate DOT code for Clusters/Node,
      depending on the hierarch_dict generated in _genhierarch
    '''
    vcount = 0
    mcount = 0
    # write clusters and node with attributes in the current toplevel cluster (frame cluster)
    for (version, milestonedict) in hierarch_dict.items():
      # create version subcluster
      self._writeVersionClusterHeader( version, vcount )
      vcount += 1
      for (milestone, ticketlist) in milestonedict.items():
        #create milestone subcluster
        self._writeMilestoneClusterHeader( milestone, mcount )
        mcount += 1
        for t in ticketlist:
          self._writeticket( t )
        #self.cmapxgen += '}'
        self._writeMilestoneClusterFooter()
      #self.cmapxgen += '}'
      self._writeVersionClusterFooter()

    # if end/start ticket is given, put them in the toplevel cluster (frame cluster)
    if self.betickets!=False:
      if self.betickets[ 'startdate' ] != None:
        self.cmapxgen += "node [shape=circle,label=\"Start %s \"] TicketStart;" % self.betickets[ 'startdate' ].date().isoformat()
      else:
        self.cmapxgen += "node [shape=circle,label=\"Start\"] TicketStart;"
      if self.betickets[ 'enddate' ] != None:
        self.cmapxgen += "node [shape=doublecircle,label=\"End %s\"] TicketEnd;"  % self.betickets[ 'enddate' ].date().isoformat()
      else:
        self.cmapxgen += "node [shape=doublecircle,label=\"End\"] TicketEnd;"

    # generate/write Note Dependencies, those must be placed in the toplevel cluster
    for (version, milestonedict) in hierarch_dict.items():
      for (milestone, ticketlist) in milestonedict.items():
        for t in ticketlist:
          self._writeticketdeps( t )

    # iv end/start ticket is given, put some extra dependencies in
    if self.betickets!=False:
      for s in self.betickets[ 'starts' ]:
        if s.hasextension( 'critical' ):
          self.cmapxgen += "TicketStart->Ticket%s [color=\"#FF0000\"];" % ( s.getfield( 'id' ) )
        else:
          self.cmapxgen += "TicketStart->Ticket%s;" % ( s.getfield( 'id' ) )
      for e in self.betickets[ 'ends' ]:
        if e.hasextension( 'critical' ):
          self.cmapxgen += "Ticket%s->TicketEnd [color=\"#FF0000\"];" % ( e.getfield( 'id' ) )
        else:
          self.cmapxgen += "Ticket%s->TicketEnd;" % ( e.getfield( 'id' ) )

  def _writeticket( self, t ):
    '''
      generate a TicketNode using the Node Prototype for Tickets
    '''
    nodehtml = GVRenderProto.ticket_gen_markup( self.macroenv, t )
    #self.cmapxgen += "node [shape=note,label=<"+nodehtml+">] Ticket"+str(t.getfield('id'))+";"
    self.cmapxgen += "node [shape=plaintext,label=<"+nodehtml+">] Ticket"+str(t.getfield('id'))+";"

  def _writeticketdeps( self, v ):
    '''
      write Ticket Dependencies for one Ticket.
      if withbufs and critical path is given, put some information in the label and
      color critical pathes
    '''
    withbufs = self.withbufs and ( v.hasextension( 'mindepbuffers' ) and v.hasextension( 'buffer' ) )
    for d in v.getextension( 'reverse_dependencies' ):
      if withbufs and ( d.getfield('id') in v.getextension('mindepbuffers') ):
        nlabel = str(v.getextension( 'buffer' ))
      else:
        nlabel = ""
      # check whether currently a new dependency was inserted
      is_added = self.macroenv.is_dependency_added( str( v.getfield('id') ), str( d.getfield( 'id' ) ) )
      is_critical = ( v.hasextension( 'critical' ) and d.hasextension( 'critical' ) )

      # TODO: activate different image if edge was added currently
      #if  is_added and is_critical:
        #edgecolstmt = ',color="#8D38C9", label=" added", fontcolor="#8D38C9" ' # Violet
      #elif is_added:
        #edgecolstmt = ',color="#F433FF", label=" added", fontcolor="#F433FF" ' # Magenta1
      if is_critical:
        edgecolstmt = ',color="#FF0000"' # red
      else:
        edgecolstmt = ''
      self.cmapxgen += "Ticket%s->Ticket%s [ label=<%s> %s ];" % (
        str( v.getfield('id') ), str( d.getfield( 'id' ) ),htmlspecialchars(nlabel), edgecolstmt )

  def _cmapxgenerate( self, ticketset ):
    '''
      generate the DOT file for Graphviz - generate a toplevel cluster Frames
      in the graph, and put version/milestone clusters and ticket nodes into it.
      append dependencies and generate the background picture and html clientside map
    '''
    # generate DOT file
    self.cmapxgen += 'strict digraph G {'
    self.cmapxgen += 'ratio="fill"; nranksep="0.01"; nodesep="0.10"; fixedsize="true"; center=true; rankdir=TB;'
    self.cmapxgen += 'graph [fontsize=14, style=filled, fillcolor="#FFFFFF"]; ' # graph background color
    self.cmapxgen += 'node [fontsize=9, color="#d0d0d0", fillcolor="#e0e0e0"]; '
    self.cmapxgen += 'edge [fontsize=9, color="#808080"]; '

    self.cmapxgen += 'subgraph clusterFrame { URL="'+self.FRAME_ADDR
    self.cmapxgen += '"; label="'+htmlspecialchars(self.FRAME_LABEL)+'"; fontcolor="black"; color="white"; '

    self.withbufs = ( 'withbuffer' in self.macroenv.macroargs )

    if 'notickets' not in self.macroenv.macroargs:

      hierarch_dict = self._genhierarch( ticketset )
      if len(hierarch_dict) > 0:
        self._writehierarch( hierarch_dict )

    if ('statuslegend' in self.macroenv.macroargs) or ('legends' in self.macroenv.macroargs):
      self._writeEnumLegendCluster( 'Status', trac.ticket.model.Status, 'ColorForStatus', 'ImageForStatus' )

    if ('prioritylegend' in self.macroenv.macroargs) or ('legends' in self.macroenv.macroargs):
      self._writeEnumLegendCluster( 'Priority', trac.ticket.model.Priority, 'ColorForPriority', 'ImageForPriority' )

    if ('tickettypelegend' in self.macroenv.macroargs) or ('legends' in self.macroenv.macroargs):
      # TODO: replace ColorForPriority with ColorForType
      self._writeEnumLegendCluster( 'Type', trac.ticket.model.Type, 'ColorForTicketType', 'ImageForTicketType' )

    self.cmapxgen += '}}'
    self.cmapxgen.generate()

  def _htmlgenerate_div( self, areadict, markup, rect, count ):
    '''
      generate a specific div for an area, with link/class information
    '''
    windowpos = "left:%dpx; top:%dpx;" % ( rect[ GVRenderer.RECT_LEFT ], rect[ GVRenderer.RECT_TOP ] )
    windowrect = "width:%dpx; height:%dpx;" % (
      rect[ GVRenderer.RECT_RIGHT ]-rect[ GVRenderer.RECT_LEFT ],
      rect[ GVRenderer.RECT_BOTTOM ]-rect[ GVRenderer.RECT_TOP ]
    )

    classstr = ''
    dummy = None
    href = None
    onclick = None

    # href are coded: ?<css class>?<real title>
    if areadict['href'] and areadict['href'].startswith('?'):
      dummy, classstr, href = areadict[ "href" ].split( '?', 2 )
      areadict[ "href" ] = href

    if areadict['href'] and areadict['href'].startswith('javascript'):
     onclick = areadict[ "href" ]
     href = '#'
     classstr = 'ticket_owner' # TODO: use a similar class
     areadict[ "href" ] = href

    if areadict[ "href" ] == "__dummy__":
      areadict[ "href" ] = None

    if not classstr:
      classstr = None
      windowpos += " position:absolute;"
      if areadict[ "href" ]:
        windowrect += " position:absolute;"

    # drop a tag when theres no href
    if areadict[ "href" ]:
      markup(
          tag.div( class_=classstr, style=windowpos )(
            tag.a( href=areadict[ "href" ], title=areadict[ "title" ], style=windowrect, onclick = onclick ) ) )
    else:
      markup( tag.div( class_=classstr, style=windowpos+windowrect ) )

  def _htmlgenerate( self, ticketset ):
    '''
      rewrite the client side map into divs
    '''
    # init return values
    error = False
    innermarkup = tag()
    bwidth = 640
    bheight = 200
    count = 0
    numpat = re.compile('\d+')
    try:
      # reopen Client-Side Map file
      cmapxfile = open(self.cmapxgen.cmapxfile)
      # reparse the file and transform shapes to div sections
      cmapxhtml = HTMLParser(source=cmapxfile)
      for elem in cmapxhtml:
        kind, data, pos = elem
        if kind == EventStream.START:
          name, attrs = data
          if name.lower() == "area":
            areadict = {}
            for a in attrs:
              name, value = a
              areadict[ name ] = value
            if areadict[ "shape" ].lower() == "rect":
              pos_strs = re.findall( numpat, areadict[ "coords" ] )
              pos = ( int( pos_strs[ GVRenderer.RECT_LEFT ] ),
                      int( pos_strs[ GVRenderer.RECT_TOP ] ),
                      int( pos_strs[ GVRenderer.RECT_RIGHT ] ),
                      int( pos_strs[ GVRenderer.RECT_BOTTOM ] ) )
              if ( (areadict[ "title" ] != self.FRAME_LABEL ) and ( areadict[ "href" ] != self.FRAME_ADDR) or (areadict[ "href" ].startswith('javascript')) ):
                self._htmlgenerate_div( areadict=areadict, markup=innermarkup, rect=pos, count=count )
                count+=1
              else:
                bwidth = pos[ GVRenderer.RECT_RIGHT ]
                bheight = pos[ GVRenderer.RECT_BOTTOM ]
      cmapxfile.close()
    #py 2.6
    #except Exception as e:
    #py 2.5
    except Exception, e:
      # catch everything that could be raised, avoid Exceptions in Exception Handler
      try:
        cmapxfile.close()
      except:
        pass
      innermarkup = tag.div( '%s raised in Renderer: %s ' % ( str( type( e ) ), str( e ) ) )
      error = True
    return ( innermarkup, bwidth, bheight, error )

  def render(self, ticketset):
    '''
      Use specific Extensions, check for Caching and generate
      the Client Side HTML Map/Background Image/HTML Code for the given ticketset
      if it is not cached
    '''
    self.ticketset = ticketset
    ## prepare ticketset
    ticketset.needExtension( 'reverse_dependencies' )
    ticketset.needExtension( 'duetimediffs' )
    ticketset.needExtension( 'criticalpath_simple' )
    self.betickets = "betickets" in self.ticketset.macroenv.macroargs
    if self.betickets:
      self.betickets = self.ticketset.getExtension( 'criticalpath_simple' )
      if self.betickets==None:
        self.betickets = False

    ticketset.needExtension( 'tslastchange' )
    dt = ticketset.getExtension( 'tslastchange' )
    dts = dt.strftime( '%d/%m/%y %H:%M:%S' )
    dte = dt.strftime( '%y-%m-%d_%H-%M-%S' )
    self.macroenv.mhash.update( dts )
    self.macroenv.mhash.finalize()
    self.cmapxgen = GVCMapXGen( self.macroenv, self.macroenv.mhash )
    ## generate on cache entry miss
    if not self.cmapxgen.cached:
      self._cmapxgenerate( ticketset )
    filename_png_www = self.cmapxgen.imglink
    ## reparse/generate extended html (in comparision to gv html subset)
    innermarkup, backgroundWidth, backgroundHeight, error = self._htmlgenerate( ticketset )

    # making the url unique if currently a dependency is added
    add_dependency = ''
    if (self.macroenv.get_args('ppdep_from') != None) and (self.macroenv.get_args('ppdep_to') != None):
      add_dependency = self.macroenv.get_args('ppdep_from')+'_'+self.macroenv.get_args('ppdep_to')

    forcereload =''
    if self.isForceReload() :
      forcereload = 'ppforcereload=1'
      dte += str(datetime.datetime.now().microsecond)

    if not error:
      outermarkup = tag.div( class_="project_image",
                             style='height:%dpx; width:%dpx; position:relative; background-image:url(%s?%s&%s%s)'
                                                            % ( backgroundHeight, backgroundWidth, filename_png_www, dte, add_dependency, forcereload ) )(
                            [
                              tag.div( style="position:absolute; top:1px; left:1px;" ),
                              innermarkup
                            ] )
    else:
       outermarkup = tag.div(innermarkup)

    outermarkup += tag.div( id='ppconnect_from' )
    outermarkup += tag.div( id='ppconnect_to' )
    outermarkup += tag.div( id='ppconnect' )

    # - generate html code for injection into xhtml trac site
    #   currently this seems to be the only way to support correct client-side rendering since
    #   empty <div ... /> and <a ... /> tags produced by genshi result in client-side crap
    return Markup(outermarkup.generate().render('html',encoding=None,strip_whitespace=False))

RenderRegister.add( GVRenderer, 'gvrender' )
RenderRegister.add( GVRenderer, 'default' )
RenderRegister.add( TicketsPerUserDay, 'tableticketperuserday' ) # legacy
RenderRegister.add( TicketsPerUserDay, 'tableticketsperday' ) 
RenderRegister.add( TicketTableAvsB, 'tableavsb' ) 
RenderRegister.add( ReportRenderer, 'ticketlist' )


class GVCollapsedHRenderer( GVRenderer ):
  '''
    GVRenderer Descendant Class, which doesnt show the whole Ticketset,
    but a selected subset. The selection is controled by url encoded arguments.
    It generates nodes for Versions with informations. On selection, Milestones
    for the selected Version are shown and on selection of Milestones,
    the Tickets are shown.
  '''

  ReqValueDelim = '_'

  def render(self, ticketset):
    '''
      Extend the inherited rendering method with checks for Open and Closed
      Versions and Milestones and special hashing for the cache, such that
      different parameters generate different cache ids
    '''
    # build version map, tsversions builds a sorted list
    # sort order will be used for identification
    ticketset.needExtension( 'tsversions' )
    num = 0
    self.vmapping = dict()
    for k in ticketset.getExtension( 'tsversions' ):
      self.vmapping[ k ] = str(num)
      num += 1

    # build milestone map, same as for version map
    ticketset.needExtension( 'tsmilestones' )
    num = 0
    self.mmapping = dict()
    for k in ticketset.getExtension( 'tsmilestones' ):
      self.mmapping[ k ] = str(num)
      num += 1

    self.vopen = set()
    self.vparm = ''
    self.mopen = set()
    self.mparm = ''
    self.hstate = 0
    if (self.macroenv.macroid+'_ver') in self.macroenv.tracreq.args:
      self.hstate = 1
      #self.macroenv.tracenv.log.debug( 'vopen (req)parm: '+ self.macroenv.tracreq.args.get(self.macroenv.macroid+'_ver') )
      self.vopen = sorted( str(self.macroenv.tracreq.args.get(self.macroenv.macroid+'_ver')).split( self.ReqValueDelim ) )
      #self.macroenv.tracenv.log.debug( 'vopen parm: '+ repr(self.vopen) )
      # verify at least, if all params can be processed
      vals = self.vmapping.values();
      for k in self.vopen:
        if k not in vals:
          self.vopen = []
          break
      #self.macroenv.tracenv.log.debug( 'vopen (verfied)parm: '+ repr(self.vopen) )
      self.vparm = ( self.ReqValueDelim ).join( self.vopen )
      self.macroenv.mhash.update( self.vparm )
      if ( len(self.vopen) > 0 ) and ( (self.macroenv.macroid+'_ms') in self.macroenv.tracreq.args ):
        self.hstate = 2
        #self.macroenv.tracenv.log.debug( 'mopen (req)parm: '+ self.macroenv.tracreq.args.get(self.macroenv.macroid+'_ms') )
        self.mopen = sorted( str(self.macroenv.tracreq.args.get(self.macroenv.macroid+'_ms')).split( self.ReqValueDelim ) )
        # same as for version, verify that param passed milestone "id"s can be processed
        vals = self.mmapping.values();
        for k in self.mopen:
          if k not in vals:
            self.mopen = []
            break
        #self.macroenv.tracenv.log.debug( 'mopen parm: '+ repr(self.mopen) )
        self.mparm = ( self.ReqValueDelim ).join( self.mopen )
        self.macroenv.mhash.update( self.mparm )

    self.macroenv.mhash.update( str(self.hstate) )
    # update render dependend hash
    return GVRenderer.render( self, ticketset )

  def _writehierarch( self, hierarch_dict ):
    '''
      Override the inherited _writehierarchie with a more complex one.
      Create the node/cluster layout depending on the current open version
      and milestone, map milestone names and version names to node ids.
      Create a special dependency map for Version/Milestone and Ticket dependencies
      based on the given Ticket dependencies.
    '''
    vcount = 0
    mcount = 0
    vnodemap = dict()
    mnodemap = dict()

    # create the special milestone/version/ticket dot code with
    # clusters for open versions/milestones and Nodes for closed versions/milestones
    # and tickets. Add links which can be used to Open/Close Milestones and Versions
    for (version, milestonedict) in hierarch_dict.items():
      if ( self.hstate > 0 ) and ( self.vmapping[ version ] in self.vopen ):
        href = self.macroenv.tracreq.href(self.macroenv.tracreq.path_info)
        # add version collapse link for cluster
        vlist = list(self.vopen)
        vlist.remove( self.vmapping[ version ] )
        if len(vlist)>0:
          href += '?%s_ver=%s' % ( self.macroenv.macroid, ( self.ReqValueDelim ).join( vlist ) )
          if len(self.mopen)>0:
            mlist = list(self.mopen)
            for k in milestonedict:
              if self.mmapping[ k ] in mlist:
                mlist.remove( self.mmapping[ k ] )
            if len(mlist)>0:
              href += '&amp;%s_ms=%s' % ( self.macroenv.macroid, ( self.ReqValueDelim ).join( mlist ) )
        href += '#%s' % self.macroenv.macroid
        self._writeVersionClusterHeader( version, vcount, href, 'Version: %s ' % version ) # close version
        for (milestone, ticketlist) in milestonedict.items():
          if ( self.hstate > 1 ) and ( self.mmapping[ milestone ] in self.mopen ):
            # add milestone collapse link
            href = self.macroenv.tracreq.href(self.macroenv.tracreq.path_info)
            href += '?%s_ver=%s' % ( self.macroenv.macroid, ( self.ReqValueDelim ).join( self.vopen ) )
            mlist = list(self.mopen)
            mlist.remove( self.mmapping[ milestone ] )
            if len(mlist)>0:
              href += '&amp;%s_ms=%s' % ( self.macroenv.macroid, ( self.ReqValueDelim ).join( mlist ) )
            href += '#%s' % self.macroenv.macroid
            self._writeMilestoneClusterHeader( milestone, mcount, href, 'Milestone: %s ' % version ) # close milestone
            tlist = ticketlist
            for t in ticketlist:
              self._writeticket( t )
            self.cmapxgen += '}'
          else:
            msnodeid = "Milestone"+str(mcount)
            mnodemap[ milestone ] = msnodeid
            self.cmapxgen += "node [shape=rect,label=<"
            # add milestone
            href = self.macroenv.tracreq.href(self.macroenv.tracreq.path_info)
            href += '?%s_ver=%s' % ( self.macroenv.macroid, self.vparm )
            if self.mopen:
              href += '&amp;%s_ms=%s' % ( self.macroenv.macroid, self.mparm+self.ReqValueDelim+self.mmapping[milestone] )
            else:
              href += '&amp;%s_ms=%s' % ( self.macroenv.macroid, self.mmapping[milestone] )
            href += '#%s' % self.macroenv.macroid
            self.cmapxgen += GVRenderProto.milestone_gen_markup( self.macroenv, version, milestone, ticketlist, href )
            self.cmapxgen += ">] " + msnodeid + ";"
          mcount += 1
        self._writeVersionClusterFooter()
      else:
        vernodeid = "Version"+str(vcount)
        vnodemap[ version ] = vernodeid
        self.cmapxgen += "node [shape=rect,label=<"
        # add version
        href = self.macroenv.tracreq.href(self.macroenv.tracreq.path_info)
        if self.vopen:
          href += '?%s_ver=%s' % ( self.macroenv.macroid, self.vparm+self.ReqValueDelim+self.vmapping[version] )
        else:
          href += '?%s_ver=%s' % ( self.macroenv.macroid, self.vmapping[version] )
        if self.mopen:
          href += '&amp;%s_ms=%s' % ( self.macroenv.macroid, self.mparm )
        href += '#%s' % self.macroenv.macroid
        self.cmapxgen += GVRenderProto.version_gen_markup( self.macroenv, version, milestonedict, href )
        self.cmapxgen += ">] " + vernodeid +";"
      vcount += 1

    # add additional start/end tickets
    if self.betickets!=False:
      if self.betickets[ 'startdate' ] != None:
        self.cmapxgen += "node [shape=circle,label=\"Start %s \"] TicketStart;" % self.betickets[ 'startdate' ].date().isoformat()
      else:
        self.cmapxgen += "node [shape=circle,label=\"Start\"] TicketStart;"
      if self.betickets[ 'enddate' ] != None:
        self.cmapxgen += "node [shape=doublecircle,label=\"End %s\"] TicketEnd;"  % self.betickets[ 'enddate' ].date().isoformat()
      else:
        self.cmapxgen += "node [shape=doublecircle,label=\"End\"] TicketEnd;"

    # create the dependencies based on node ids for the DOT file
    hdepmap = dict()

    # create the node dependencies and count the number of deps
    # the dep count is used for thickening the dependencies
    def ticket_to_depnode( t ):
      '''
        lookup the node id for this ticket which is either
          a version node which contains t or
          a milestone node which contains t or
          the ticketnode when containing version and milestone are open
      '''
      if ( self.hstate > 0 ) and ( self.vmapping[ t.getfielddef( 'version', '' ) ] in self.vopen ):
        if ( self.hstate > 1 ) and ( self.mmapping[ t.getfielddef( 'milestone', '' ) ] in self.mopen ):
          return 'Ticket'+str(t.getfield( 'id' ))
        else:
          return mnodemap[ t.getfielddef( 'milestone', '' ) ]
      else:
        return vnodemap[ t.getfielddef( 'version', '' ) ]

    def addhdepmap( tdep, ddep, crit, max_deps ):
      if tdep!=ddep:
        if tdep in hdepmap:
          if ddep in hdepmap[ tdep ]:
            hdepmap[ tdep ][ ddep ][ 'count' ] += 1
            hdepmap[ tdep ][ ddep ][ 'crit' ] |= crit
            if max_deps < hdepmap[ tdep ][ ddep ][ 'count' ]:
              max_deps = hdepmap[ tdep ][ ddep ][ 'count' ]
          else:
            hdepmap[ tdep ][ ddep ] = { 'count': 1, 'crit': crit }
        else:
          hdepmap[ tdep ] = { ddep: { 'count': 1, 'crit': crit } }
      return max_deps

    max_deps = 1

    # build the dependency map and count the number of dependencies
    # between nodes (directed!!!)
    for (version, milestonedict) in hierarch_dict.items():
      for (milestone, ticketlist) in milestonedict.items():
        for t in ticketlist:
          for d in t.getextension( 'reverse_dependencies' ):
            crit = t.hasextension( 'critical' ) and d.hasextension( 'critical' )
            tdep = ticket_to_depnode( t )
            ddep = ticket_to_depnode( d )
            max_deps = addhdepmap( tdep, ddep, crit, max_deps )

    # fill end/start ticket dependencies into the hdepmap
    if self.betickets!=False:
      for s in self.betickets[ 'starts' ]:
        max_deps = addhdepmap( 'TicketStart', ticket_to_depnode( s ), s.hasextension( 'critical' ), max_deps )
      for e in self.betickets[ 'ends' ]:
        max_deps = addhdepmap( ticket_to_depnode( e ), 'TicketEnd', e.hasextension( 'critical' ), max_deps )

    def scale_linewidth( depcount ):
      '''
        scale the linewidth between 1 and 3 depending on the current
        maximum dependencies in the current graph or default to 1 when
        theres a maximum of 1
      '''
      if max_deps > 1:
        return math.floor((float(depcount)/max_deps)*3)
      else:
        return 1

    # write _node_ dependencies, scale edge linewidth by dependency number
    for (tdep,v) in hdepmap.items():
      for (ddep,c) in v.items():
        if hdepmap[tdep][ddep]['crit']:
          edgecolstmt = ',color="#FF0000"'
        else:
          edgecolstmt = ''
        self.cmapxgen += '%s->%s [style="setlinewidth(%s)"%s];' % (
          tdep, ddep, str(scale_linewidth( hdepmap[tdep][ddep]['count'] )), edgecolstmt )


RenderRegister.add( GVCollapsedHRenderer, 'gvhierarchical' )
#RenderRegister.add( GVCollapsedHRenderer, 'default' )
RenderRegister.add( BurndownChartTickets, 'burndowntickets' )
#RenderRegister.add( HierarchicalRenderer2, 'hiera')
RenderRegister.add( GroupStatsBar, 'groupstatsbar')

class ppRender():
  '''
    Renderer Abstraction
    This Class simply selects another (RenderImpl) Renderer based
    on the passed KW key:value pair for renderer.
    The Matching or Default Renderer is selected from those Classes,
    in the Render Register.
  '''
  def __init__(self, macroenv ):
    '''
      determine concrete renderer
    '''
    self.macroenv = macroenv
    renderer = macroenv.macrokw.get('renderer')
    if ( renderer == '' ) or ( renderer not in RenderRegister.keys() ):
      macroenv.tracenv.log.warning('Unknown or no renderer given: %s ' % (renderer, ) )
      renderer = 'default'
    ConcreteRenderer = RenderRegister.get( renderer )
    self.concreteRenderer = ConcreteRenderer( self.macroenv )

  def render(self, ticketset):
    return self.concreteRenderer.render( ticketset )

  def getHeadline(self):
    return self.concreteRenderer.getHeadline()


def dummy( *args ):
  '''
    dummy method used as place holder
  '''
  pass