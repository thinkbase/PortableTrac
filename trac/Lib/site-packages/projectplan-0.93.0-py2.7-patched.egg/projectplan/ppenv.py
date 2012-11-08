# -*- coding: utf-8 -*-

import re
import datetime
import os

from trac.core import *
from trac.config import *
from trac.wiki.api import parse_args
from ppcache import ppFSFileCache

from trac.db import get_column_names
import time


import trac.ticket.model

class PPConstant():
  dynamic_content_suffix = 'projectplan_dynamic'
  cache_content_suffix = 'pp_cached'
  change_ticket_suffix = 'pp_ticket_changes'
  definisection_name = 'pp_options'
  RelDocPath = 'images'
  ImagePattern = re.compile( '.*(\.(png|gif|jpg|jpeg))', re.IGNORECASE )

class PPImages( ):
  selectablekw = None
  env = None
  
  @classmethod
  def absbasepath( cls ):
    '''
      Return the Absolute Basepath for the Path Selectables
    '''
    dp = os.path.normpath( PPConstant.RelDocPath )
    from pkg_resources import resource_filename
    htdp = os.path.abspath(os.path.normpath(resource_filename(__name__, 'htdocs')))
    return os.path.join( htdp, dp )

  @classmethod
  def collectimages(cls, dir, files):
    '''
      recursive search for images
    '''
    #dir = os.path.abspath(dir)
    for file in [file for file in os.listdir(dir) if not file in [".",".."]]:
      nfile = os.path.join(dir,file)
      if os.access(nfile,os.R_OK):
        if os.path.isdir(nfile):
          cls.collectimages(nfile, files)
        else:
          # TODO: filter files already at this point
          files.append(nfile)

  @classmethod
  def selectable( cls, defaultvalue, env ):
    '''
      Return a dict of Selectables (and absolute filenames as values)
    '''
    dirlist = []
    cls.env = env
    if cls.selectablekw == None:
      cls.selectablekw = dict()
      p = cls.absbasepath()
      try:
        if os.path.isdir( p ):
          cls.collectimages(p,dirlist) # collect all accessable images
        else:
          dirlist = []
        for f in dirlist:
          f_short = f[ len(p)+1: ] # kind of a hack
          cls.selectablekw[ f_short ] = f # os.path.join( p, f )
      finally:
        pass
      if defaultvalue not in cls.selectablekw:
        cls.selectablekw[ defaultvalue ] = ''
    return cls.selectablekw

class PPOption():
  '''
    Base Class for (Change/Save/Load/Show)-able Options
  '''
  def __init__( self, key, defval, section, catid, groupid, doc ):
    '''
      Initialize the base Option with some basic Values:
        * key - for reading and writing this Options
        * defval - the default value if non-existent or invalid
        * section - the config section where (key,value) are written to
        * catid - the category page for AdminPanel
        * groupid - the group id for grouped values
        * doc - Documentation for the Option Value/Key shown in AdminPanel
    '''
    if key:
      self.key = key
    else:
      raise Exception('empty key not allowed')
    self.defval = defval
    self.section = section
    self.catid = catid
    self.groupid = groupid
    self.doc = doc

  def get( self ):
    '''
      getter for Optionvalue
    '''
    raise NotImplementedError()

  def set( self, value ):
    '''
      setter for Optionvalue
    '''
    raise NotImplementedError()

class PPSingleValOption( PPOption ):
  '''
    Basic Single Value Option
  '''
  def __init__( self, env, key, defval, section=PPConstant.definisection_name, catid=None, groupid=None, doc="Not Documented" ):
    '''
      Initialize Base Option and add the env for setting/getting Options
    '''
    PPOption.__init__( self, key, defval, section, catid, groupid, doc )
    self.env = env

  def get( self ):
    '''
      std getter using env.config.get
    '''
    return self.env.config.get( self.section, self.key, self.defval )

  def set( self, value ):
    '''
      std setter using env.config.set
    '''
    self.env.config.set( self.section, self.key, value )

class PPSingleSelOption( PPSingleValOption ):
  '''
    Basic Single Value Selection Option
  '''
  def inselectable( self, value ):
    '''
      Check wether a value is in the Selectables
    '''
    return ( value in self.selectable() )

  def selectable( self ):
    '''
      Return a list or dict of Selectables
    '''
    raise NotImplementedError()

class PPSingleConOption( PPSingleValOption ):
  '''
    Basic Single Value Constrained Option
  '''

  def get( self ):
    '''
      get the verified value or the defaultvalue
    '''
    val = PPSingleValOption.get( self )
    if self.verifyvalue( val ):
      return val
    else:
      return self.defval

  def set( self, value ):
    '''
      set the verified value or the defaultvalue
    '''
    if self.verifyvalue( value ):
      PPSingleValOption.set( self, value )
    else:
      PPSingleValOption.set( self, self.defval )

  def verifyvalue( self, value ):
    '''
      verify the value
    '''
    raise NotImplementedError()

class PPListOfOptions( PPOption ):
  '''
    Basic List of Options
  '''

  def keys( self ):
    '''
      Return a list of Keys for the list of Options
    '''
    raise NotImplementedError()

  def get_val_for( self, subkey ):
    '''
      getter for a single option value in the list of options
    '''
    raise NotImplementedError()

  def set_val_for( self, subkey, value ):
    '''
      setter for a single option value in the list of options
    '''
    raise NotImplementedError()

  def get( self ):
    '''
      getter for a list of keys and values for the list of options
    '''
    retdict = {}
    for k in self.keys():
      retdict[ k ] = self.get_val_for( k )
    return retdict

  def set( self, indict ):
    '''
      setter for a list of keys and values for the list of options
    '''
    for k in self.keys():
      if k in indict:
        self.set_val_for( indict[ k ] )

class PPListOfSelOptions( PPListOfOptions ):
  '''
    Base Class for a List of Selection Options
  '''

  def inselectable( self, value ):
    '''
      Check wether calue is in the Selectables
    '''
    return ( value in self.selectable() )

  def selectable( self ):
    '''
      Return a list or dict of Selectables
    '''
    raise NotImplementedError()

class PPHTDPathSelOption( PPSingleSelOption ):
  '''
    HTDocs Path Selection Option Class
  '''
  RelDocPath = ''

  def __init__( self, env, key, defval, section=PPConstant.definisection_name, catid=None, groupid=None, doc="Not Documented" ):
    '''
      Initialize the Base Singel Selection Option
    '''
    PPSingleSelOption.__init__( self, env, key, defval, section, catid, groupid, doc )
    self.selectablekw = None
    self.env = env
    self.RelDocPath = PPConstant.RelDocPath #new

  @classmethod
  def absbasepath( cls ):
    '''
      Return the Absolute Basepath for the Path Selectables
    '''
    #dp = os.path.normpath( cls.RelDocPath )
    #from pkg_resources import resource_filename
    #htdp = os.path.abspath(os.path.normpath(resource_filename(__name__, 'htdocs')))
    #return os.path.join( htdp, dp )
    return PPImages.absbasepath()

  def collectimages(self,dir, files):
    '''
      recursive search for images
    '''
    #dir = os.path.abspath(dir)
    for file in [file for file in os.listdir(dir) if not file in [".",".."]]:
      nfile = os.path.join(dir,file)
      if os.access(nfile,os.R_OK):
        if os.path.isdir(nfile):
          self.collectimages(nfile, files)
        else:
          # TODO: filter files already at this point
          files.append(nfile)

  def selectable( self ):
    '''
      Return a dict of Selectables (and absolute filenames as values)
    '''
    dirlist = []
    if self.selectablekw == None:
      self.selectablekw = dict()
      p = self.absbasepath()
      try:
        if os.path.isdir( p ):
          self.collectimages(p,dirlist) # collect all accessable images
        else:
          dirlist = []
        for f in dirlist:
          f_short = f[ len(p)+1: ] # kind of a hack
          self.selectablekw[ f_short ] = f # os.path.join( p, f )
      finally:
        pass
      if self.defval not in self.selectablekw:
        self.selectablekw[ self.defval ] = ''
    return self.selectablekw

class PPListOfHTDPathSelOptions( PPListOfSelOptions ):
  '''
    List of HTDoc Path Selection Options
  '''

  def selector( self ):
    '''
      Return a Selector (PPHTDPathSelOption) which is used for
      accessing the RelDocPath and selectable() attributes
    '''
    raise NotImplementedError()

  def selectable( self ):
    '''
      Return the Selectables for the Selector
    '''
    return self.selector().selectable()

class PPImageSelOption(PPHTDPathSelOption):
  '''
    HTDoc Image Path Selection Option
  '''

  def selectable( self ):
    '''
      Return a dict of Selectable Images (ending with png/gif/jpg/jpeg) and
      the Default Value if not existend in the Selectables
    '''
    if self.selectablekw == None:
      seldict = PPHTDPathSelOption.selectable( self )
      for ( e, f ) in seldict.items():
        if ( not os.path.isfile( f ) ) or ( not re.match( PPConstant.ImagePattern, e ) ):
          if e != self.defval:
            del seldict[ e ]
    return PPHTDPathSelOption.selectable( self )

class PPListOfImageSelOptions( PPListOfHTDPathSelOptions ):
  '''
    List of HTDoc Image Path Selection Options
    (for Image dependend checks in AdminPanel)
  '''
  pass

class PPBooleanSwitchOption(PPSingleSelOption):
  '''
    Selectable Boolean Option
  '''
  def selectable( self ):
    '''
      Return a List of possible Values
    '''
    return [ 'enabled', 'disabled' ]

class PPDateFormatOption(PPSingleSelOption):
  '''
    Selectable DateFormat Option
  '''
  def selectable( self ):
    '''
      Check wether the value is in the List of possible Values
    '''
    return [ 'DD/MM/YYYY', 'MM/DD/YYYY', 'DD.MM.YYYY' ]

class PPActivateColumnOption(PPSingleSelOption):
  '''
    Selectable DateFormat Option
  '''
  def selectable( self ):
    '''
      Check wether the value is in the List of possible Values
    '''
    return [ 'on', 'off' ]

  def get( self ):
    '''
      std getter using env.config.get
    '''
    try:
      return self.env.config.get( self.section, self.key, self.defval )
    except:
      return 'on' # standard


class PPHTMLColorOption(PPSingleConOption):
  '''
    HTML Color Option
  '''
  def verifyvalue( self, value ):
    '''
      Check wether the value has the Format #<6 hex digits>
    '''
    return ( re.match( '#[0-9A-Fa-f]{6}', value )!=None )

class PPIntegerOption(PPSingleConOption):
  '''
    Integer Option
  '''
  def verifyvalue( self, value ):
    '''
      Check wether the value is an Integer value
    '''
    res = True
    try:
      int(value)
    except TypeError:
      res = False
    return res

class PerTracModelEnumColor( PPListOfOptions ):
  '''
    Base Class for List of HTML Color Options for a
    trac.ticket.model.AbstractEnum descendant
  '''

  enumerator_cls = trac.ticket.model.AbstractEnum

  def __init__( self, env, key, defval, section=PPConstant.definisection_name, catid=None, groupid=None, doc='"%s" Not Documented' ):
    '''
      Initialize Single Option which holds the Color Option Key:Value pairs
    '''
    PPListOfOptions.__init__( self, key, defval, section, catid, groupid, doc )
    self._internalOption = PPSingleValOption( env, self.key, '' )

  def keys( self ):
    '''
      Return possible Keys Enumeration Keys, currently set in Trac.
      Like Priority, Severity, and so on.
    '''
    return [ e.name for e in self.enumerator_cls.select( self._internalOption.env ) ]

  def get( self ):
    '''
      Get a Key:Value Dict for Key:HTML Code pairs
    '''
    retdict = {}
    for k in self.keys():
      retdict[ k ] = self.defval
    opts = self._internalOption.get()
    udict = {}
    if opts:
      for entry in opts.split(','):
        (k,v) = entry.strip('"').split( '=', 1 )
        udict[ k ] = v
    retdict.update( udict )
    return retdict

  def set( self, indict ):
    '''
      Set a Key:Value Dict for Key:HTML Code pairs.
      Keys not in current Enumeration will be dropped, Keys not set but in current enumeration
      will be set to defval.
    '''
    wdict = {}
    for k in self.keys():
      if ( k in indict ) and indict[ k ] and ( indict[ k ] != self.defval ):
        wdict[ k ] = indict[ k ]
    if len(wdict) > 0:
      setstr = '"'+ reduce( lambda x, y: x+'","'+y, map( lambda k: k+"="+wdict[ k ], wdict.keys() ) ) +'"'
    else:
      setstr = ''
    self._internalOption.set( setstr )

  def get_val_for( self, subkey ):
    '''
      Return a single HTML Code for a given Enumeration Key
    '''
    gdict = self.get()
    if subkey in gdict:
      return gdict[ subkey ]
    else:
      return self.defval

  def set_val_for( self, subkey, value ):
    '''
      Set a single HTML Code for a given Enumeration Key. Same behavior as for set
    '''
    gdict = self.get()
    if re.match( '#[0-9A-Fa-f]{6}', value ):
      gdict[ subkey ] = value
    else:
      gdict[ subkey ] = self.defval
    self.set( gdict )

class PerTracModelEnumImage( PPListOfImageSelOptions ):
  '''
    Base Class for List of selectable Image Options for a
    trac.ticket.model.AbstractEnum descendant
  '''

  enumerator_cls = trac.ticket.model.AbstractEnum

  def __init__( self, env, key, defval, section=PPConstant.definisection_name, catid=None, groupid=None, doc='"%s" Not Documented' ):
    '''
      Initialize Internal vars for Key:Value Storage
    '''
    PPListOfSelOptions.__init__( self, key, defval, section, catid, groupid, doc )
    self._internalOption = PPImageSelOption( env, key, defval )
    self._internalKeys = None
    self.env = env

  def selector( self ):
    '''
      Return the Internal Single Selector Option used for Selection
      of Option Values
    '''
    return self._internalOption

  def keys( self ):
    '''
      Return a Dict with Enumeration Keys for this Option
    '''
    if self._internalKeys is not None:
      return self._internalKeys
    else:
      self._internalKeys = [ e.name for e in self.enumerator_cls.select( self.env ) ]
      return self._internalKeys

  def get_val_for( self, subkey ):
    '''
      Return the Selected Value (Image) for a given Enumeration Key
    '''
    if subkey in self.keys():
      res = self.env.config.get( self.section, self.key+subkey, self.defval )
      if not self.inselectable( res ):
        res = self.defval
    else:
      res = self.defval
    return res

  def set_val_for( self, subkey, value ):
    '''
      Set the Value for a given Enumeration Key, if it is selectable, else default to defval
    '''
    if subkey in self.keys():
      if not self.inselectable( value ):
        value = self.defval
      self.env.config.set( self.section, self.key+subkey, value )

class PPStatusColorOption( PerTracModelEnumColor ):
  '''
    Per Status Color Option
  '''
  enumerator_cls = trac.ticket.model.Status

class PPPriorityColorOption( PerTracModelEnumColor ):
  '''
    Per Priority Color Option
  '''
  enumerator_cls = trac.ticket.model.Priority

class PPTicketTypeColorOption( PerTracModelEnumColor ):
  '''
    Per Ticket Type Color Option
  '''
  enumerator_cls = trac.ticket.model.Type 

class PPStatusImageOption( PerTracModelEnumImage ):
  '''
    Per Status Image Option
  '''
  enumerator_cls = trac.ticket.model.Status

class PPTicketTypeImageOption( PerTracModelEnumImage ):
  '''
    Per TypeImage Option
  '''
  enumerator_cls = trac.ticket.model.Type

class PPPriorityImageOption( PerTracModelEnumImage ):
  '''
    Per Priority Image Option
  '''
  enumerator_cls = trac.ticket.model.Priority

class PPConfiguration():
  '''
    ProjectPlan Configuration which Loads/Saves/Manages the Options and
    List of Options.
    Single Value Options are placed in self.flatconf and
    List of Options in self.listconf, both are free for access but
    PPConfiguration wraps some checks around so try to use the PPConfiguration
    methods instead of accessing the Options objects directly.
  '''

  def __init__( self, env ):
    '''
      Initialize the Option (flatconf) and List of Option (listconf) mappings.
      Load the Values.
    '''
    self.env = env
    # <attr>: ( <section>, <key>, <default value> )
    self.flatconf = {}
    # <attr>: ( <section suffix>, <key_list function>, <default value>, <default for non exisiting value> )
    self.listconf = {}
    self.load()

  # non-list attribute getter/setter defaults
  def get_defaults( self, n, fallback):
      return {
                         'ticket_owned_image': 'crystal_project/16x16/user/gold.png',
                         'ticket_notowned_image': 'crystal_project/16x16/user/blue.png',
                         'ticket_multiple_owner_image': 'crystal_project/16x16/user/group.png',
                         #
                         'ticket_ontime_image': 'crystal_project/16x16/calendar/xdays.png',
                         'ticket_overdue_image': 'crystal_project/16x16/calendar/timespan.png',
                         }.get(n, fallback) # fallback to prevent images if unknown state

  # non-list attribute getter/setter
  def get( self, n ):
    '''
      Single Option Value Getter: get value for Key n
    '''
    if n in self.flatconf:
      val = self.flatconf[ n ].get()
      if val == 'none':
        return self.get_defaults( n, val )
      else:
        return val
    else:
      raise Exception( "Option %s not found" % n )
  
  def get_ticket_custom( self, option_name ):
    '''
      read directly from the trac.ini file
    '''
    return self.env.config.get( 'ticket-custom', option_name, None )


  def set( self, n, v ):
    '''
      Single Option Value Setter: set value v for Key n
    '''
    if n in self.flatconf:
      self.flatconf[ n ].set( v )
    else:
      raise Exception( "Option %s not found" % n )

  def get_map_defaults( self, n , k, color ):
    '''
      get default values for attributes of standard trac installation
    '''
    # TODO: out sourcing of conf information
    if 'ColorForPriority' == n :
      return {     'blocker': 'red',
                         'critical': '#f88017', # darkorange
                         'major': 'yellow',
                         'minor': '#fcdfff', # thistle1
                         'trivial': '#c2dfff' # slategray1
                         }.get(k, 'grey')
    elif 'ColorForStatus' == n :
      return {     'assigned': '#F0F0F0',
                         'new': '#909090',
                         'reopened': '#F0F090',
                         'closed': '#C0F0C0'
                         }.get(k, self.get('ColorForStatusNE'))
    elif 'ImageForPriority' == n :
      return {     'blocker': 'crystal_project/16x16/arrow/priority1up2.png',
                         'critical': 'crystal_project/16x16/arrow/priority2up1.png',
                         'major': 'crystal_project/16x16/arrow/priority3right.png',
                         'minor': 'crystal_project/16x16/arrow/priority4down1.png',
                         'trivial': 'crystal_project/16x16/arrow/priority5down2.png'
                         }.get(k, 'none') # fallback to prevent images if unknown state
    elif 'ImageForStatus' == n :
      return {     'new': 'crystal_project/16x16/state/new.png',
                         'assigned': 'crystal_project/16x16/state/kate.png',
                         'closed': 'crystal_project/16x16/state/ok.png',
                         'reopened': 'crystal_project/16x16/state/restart.png'
                         }.get(k, 'none') # fallback to prevent images if unknown state
    elif 'ImageForTicketType' == n :
      return {     'task': 'crystal_project/16x16/type/settings.png',
                         'defect': 'crystal_project/16x16/type/flag.png',
                         'enhancement': 'crystal_project/16x16/type/enhancements2.png'
                         }.get(k, 'none') # fallback to prevent images if unknown state
    else :
      return color

  def get_map( self, n ):
    '''
      List of Options Value Getter: get a dict of values and option keys for (list) Key n
    '''
    if n in self.listconf:
      return self.listconf[ n ].get()
    else:
      raise Exception( "List of Options for %s not found" % n )

  def get_map_val( self, n, k ):
    '''
      Single Option Value Getter: get value for Key k in List n
    '''
    if n in self.listconf:
      val = self.listconf[ n ].get_val_for( k )
      if val.upper() == 'NONE' : # default values
        val = self.get_map_defaults( n, k, val )
      return val
    else:
      raise Exception( "List of Options for %s not found" % n )

  def set_map( self, n, v ):
    '''
      List of Options Value Setter: set a dict of option keys and values for (list) Key n
    '''
    if n in self.listconf:
      self.listconf[ n ].set( v )
    else:
      raise Exception( "List of Options for %s not found" % n )

  def set_map_val( self, n, k, v ):
    '''
      Single Option Value Setter: set value v for Key k in List n
    '''
    if n in self.listconf:
      self.listconf[ n ].set_val_for( k, v )
    else:
      raise Exception( "List of Options for %s not found" % n )

  def load( self ):
    '''
      Initialize the Options and List of Options and load the Values (or Defaults)
    '''
    # Ticket-Custom Field Mappings (no catid/grpid -> not for panel)
    self.flatconf[ 'custom_dependency_field' ] = PPSingleValOption(
      self.env, 'custom_dependency_field', u'dependencies' )
    
    self.flatconf[ 'custom_reverse_dependency_field' ] = PPSingleValOption(
      self.env, 'custom_reverse_dependency_field', u'dependenciesreverse' )

    self.flatconf[ 'custom_due_assign_field' ] = PPSingleValOption(
      self.env, 'custom_due_assign_field', u'due_assign' )

    self.flatconf[ 'custom_due_close_field' ] = PPSingleValOption(
      self.env, 'custom_due_close_field', u'due_close' )

    # Basic Options
    self.flatconf[ 'cachepath' ] = PPSingleValOption(
      self.env, 'cachepath', u'/tmp/ppcache', catid='General', groupid='Cache', doc="""
      Path for File based Caching (mainly used for Image/HTML Rendering speedup).\n
      \n
      Warning: the cache root directory must be a real directory, not a link\n
      Warning: after changing this option you need to manually delete the old cache
      """ )

    self.flatconf[ 'cachedirsize' ] = PPIntegerOption(
      self.env, 'cachedirsize', u'1', catid='General', groupid='Cache', doc="""
      Cache lookup Directory Size\n
      Caching can produce an enormous amount of Files which puts some pressure on
      the underlying Filesystem. Directory lookup and File lookup/creation may be speed up
      with multiple smaller Directory nodes.\n
      (depends on the Filesystem and amount of Files created)\n
      0 = off, all Files will be placed into the cache path\n
      1 - digest length for used hash = use max. 16^(cachedirsize) prefix directories\n
      \n
      Warning: after changing this option you need to manually delete the old cache
      """ )

    self.flatconf[ 'dotpath' ] = PPSingleValOption(
      self.env, 'dot_executable', u'/usr/bin/dot', catid='General', groupid='Renderer', doc="""
      Executable Path for the Graphiz dot Program
      """ )

    self.flatconf[ 'dotfixfparm' ] = PPBooleanSwitchOption(
      self.env, 'dotfixfparm', u'disabled', catid='General', groupid='Renderer', doc="""
      First Parameter Fix, visit http://trac-hacks.org/wiki/ProjectPlanPlugin/DotCompatibility for
      further information.
      """ )

    # Ticket Custom Options
    self.flatconf[ 'ticketassignedf' ] = PPDateFormatOption(
      self.env, '%s.value' % self.get( 'custom_due_assign_field' ),
      u'DD/MM/YYYY', section='ticket-custom', catid='General', groupid='Tickets', doc="""
      DateTime Format which will be used for Calculating the Assign Date
      """ )
    self.flatconf[ 'ticketclosedf' ] = PPDateFormatOption(
      self.env, '%s.value' % self.get( 'custom_due_close_field' ),
      u'DD/MM/YYYY', section='ticket-custom', catid='General', groupid='Tickets', doc="""
      DateTime Format which will be used for Calculating the Closing Date
      """ )


    self.flatconf[ 'max_ticket_number_at_filters' ] = PPIntegerOption(
      self.env, 'max_ticket_number_at_filters', u'1000', catid='General', groupid='Query', doc="""
      How many tickets should be get at maximum during one query?\n
      If not all tickets appear within your ticket representations, then increase this number.\n
      The default of Trac is 100, while the default of ProjectPlanPlugin is 1000.
      """ )

    # TODO: Add Configuration
    # Ticket Visualizations Options
    #self.flatconf[ 'custom_show_tickettype' ] = PPActivateColumnOption(
      #self.env, '%s.value' % self.get( 'custom_show_tickettype'),
      #u'on', section='ticket-custom', catid='General', groupid='Tickets', doc="""
      #XXX1
      #""" )
    #self.flatconf[ 'custom_show_state' ] = PPActivateColumnOption(
      #self.env, '%s.value' % self.get( 'custom_show_state'),
      #u'on', section='ticket-custom', catid='General', groupid='Tickets', doc="""
      #XXX2
      #""" )

    # Color/Image Options
    self.flatconf[ 'version_fillcolor' ] = PPHTMLColorOption(
      self.env, 'version_fillcolor', u'#FFFFE0', catid='Color', groupid='Non Ticket Elements', doc="""
      Version Cluster Fillcolor
      """ )

    self.flatconf[ 'version_fontcolor' ] = PPHTMLColorOption(
      self.env, 'version_fontcolor', u'#0000FF', catid='Color', groupid='Non Ticket Elements', doc="""
      Version Cluster Font Color
      """ )

    self.flatconf[ 'version_color' ] = PPHTMLColorOption(
      self.env, 'version_color', u'#0000FF', catid='Color', groupid='Non Ticket Elements', doc="""
      Version Cluster Frame Color
      """ )

    self.flatconf[ 'milestone_fillcolor' ] = PPHTMLColorOption(
      self.env, 'milestone_fillcolor', u'#F5F5F5', catid='Color', groupid='Non Ticket Elements', doc="""
      Milestone Cluster Fillcolor
      """ )

    self.flatconf[ 'milestone_fontcolor' ] = PPHTMLColorOption(
      self.env, 'milestone_fontcolor', u'#0000FF', catid='Color', groupid='Non Ticket Elements', doc="""
      Milestone Cluster Font Color
      """ )

    self.flatconf[ 'milestone_color' ] = PPHTMLColorOption(
      self.env, 'milestone_color', u'#0000FF', catid='Color', groupid='Non Ticket Elements', doc="""
      Milestone Cluster Frame Color
      """ )

    self.flatconf[ 'ticket_ontime_color' ] = PPHTMLColorOption(
      self.env, 'ticket_ontime_color', u'#FFFF00', catid='Color', groupid='Tickets', doc="""
        Color for: Ticket is on Time
      """ )

    self.flatconf[ 'ticket_overdue_color' ] = PPHTMLColorOption(
      self.env, 'ticket_overdue_color', u'#FF0000', catid='Color', groupid='Tickets', doc="""
        Color for: Ticket is Over Due
      """ )

    self.flatconf[ 'ticket_notowned_color' ] = PPHTMLColorOption(
      self.env, 'ticket_notowned_color', u'#FFFFFF', catid='Color', groupid='Tickets', doc="""
        Color for: Ticket is not Owned by current User
      """ )

    self.flatconf[ 'ticket_owned_color' ] = PPHTMLColorOption(
      self.env, 'ticket_owned_color', u'#FF0000', catid='Color', groupid='Tickets', doc="""
        Color for: Ticket is Owned by current User
      """ )

    self.flatconf[ 'ticket_ontime_image' ] = PPImageSelOption(
      self.env, 'ticket_ontime_image', u'none', catid='Image', groupid='Tickets', doc="""
        Symbol for: Ticket is on Time
      """ )

    self.flatconf[ 'ticket_overdue_image' ] = PPImageSelOption(
      self.env, 'ticket_overdue_image', u'none', catid='Image', groupid='Tickets', doc="""
        Symbol for: Ticket is Over Due
      """ )

    self.flatconf[ 'ticket_notowned_image' ] = PPImageSelOption(
      self.env, 'ticket_notowned_image', u'none', catid='Image', groupid='Tickets', doc="""
        Symbol for: Ticket is not Owned by current User
      """ )

    self.flatconf[ 'ticket_multiple_owner_image' ] = PPImageSelOption(
      self.env, 'ticket_multiple_owner_image', u'none', catid='Image', groupid='Tickets', doc="""
        Symbol for: Ticket is Owned by several Users
      """ )

    self.flatconf[ 'ticket_owned_image' ] = PPImageSelOption(
      self.env, 'ticket_owned_image', u'none', catid='Image', groupid='Tickets', doc="""
        Symbol for: Ticket is Owned by current User
      """ )

    self.flatconf[ 'ColorForStatusNE' ] = PPHTMLColorOption(
      self.env, 'color_for_ne_status', u'#C9C9C9', catid='Color', groupid='Status', doc="""
      Color for Non-Existing/New Status
      """ )

    self.flatconf[ 'ColorForPriorityNE' ] = PPHTMLColorOption(
      self.env, 'color_for_ne_priority', u'none', catid='Color', groupid='Priority', doc="""
      Color for Non-Existing/New Priority
      """ )

    self.flatconf[ 'ColorForTicketType' ] = PPHTMLColorOption(
      self.env, 'color_for_ticket_type', u'none', catid='Color', groupid='Type', doc="""
      Color for Ticket Type
      """ )

    self.listconf[ 'ColorForStatus' ] = PPStatusColorOption(
      self.env, 'colorforstatus', u'none', catid='Color', groupid='Status', doc="""
      HTML Color for rendering Status "%s"
      """ )

    self.listconf[ 'ColorForPriority' ] = PPPriorityColorOption(
      self.env, 'colorforpriority', self.get( 'ColorForPriorityNE' ), catid='Color', groupid='Priority', doc="""
      HTML Color for rendering Priority "%s"
      """ )

    self.listconf[ 'ColorForTicketType' ] = PPTicketTypeColorOption(
      self.env, 'colorfortickettype', self.get( 'ColorForTicketType' ), catid='Color', groupid='Type', doc="""
      HTML Color for rendering Ticket Type"%s"
      """ )

    self.listconf[ 'ImageForStatus' ] = PPStatusImageOption(
      self.env, 'image_for_status_', u'none', catid='Image', groupid='Status', doc="""
      Image for Status "%s"
      """ )

    self.listconf[ 'ImageForPriority' ] = PPPriorityImageOption(
      self.env, 'image_for_priority_', u'none', catid='Image', groupid='Priority', doc="""
      Image for Priority "%s"
      """ )

    self.listconf[ 'ImageForTicketType' ] = PPTicketTypeImageOption(
      self.env, 'image_for_ticket_type_', u'none', catid='Image', groupid='Type', doc="""
      Image for Ticket Type "%s"
      """ )

    # TODO: complete information
    #self.listconf[ 'ImageForStatus' ] = PPStatusImageOption(
    #  self.env, 'image_for_connector_', u'none', catid='Image', groupid='Connector', doc="""
    #  Image for Connector "%s"
    #  """ )

  def save( self ):
    '''
      Save all Changes to the Options and List of Options
    '''
    self.env.config.save()

class PPEnv():
  '''
    Project Plan Environment
    containing references and so on, for most used objects and values like
    macro arguments, trac environment and request...
  '''
  # TODO: move to constants
  connectimg = 'crystal_project/16x16/conf/configure.png'
  PPConstant = PPConstant()
  
  def __init__( self, env, req, content ):
    '''
      Initialize the Envoironment
    '''
    # parse passed macro arguments
    args, kw = parse_args( content )
    self.macroid = str( kw.get('macroid') ) or '1';
    self.macroargs = args
    
    # replace generic values    
    for k in kw.keys():
      kw[k] = kw[k].replace('$user', req.authname)
    self.macrokw = kw
    
    # set constants
    self.const = PPConstant
    # set trac environment, request
    self.tracenv = env
    self.tracreq = req
    # load configuration items
    self.conf = PPConfiguration(env)
    # create cache
    self.cache = ppFSFileCache( self.conf.get( 'cachepath' ),
                                datetime.date.today().isoformat(),
                                int(self.conf.get( 'cachedirsize' )) )
    # initialize the cache hash value with environment settings
    self.mhash = self.cache.newHashObject()
    self.mhash.update( content )
    self.mhash.update( self.macroid )
    self.mhash.update( self.tracreq.authname )
    self.mhash.update( str( datetime.date.today() ) )

  def get_args( self , argname):
    '''
      get http url parameter
    '''
    try:
      return self.tracreq.args.get( argname )
    except:
      return None

  def has_args( self , argname):
    '''
      check existence of http url parameter
    '''
    try:
      self.tracreq.args.get( argname )
      return True
    except:
      return False

  def is_dependency_added( self, dep_from, dep_to ) :
    '''
      checks if a specific dependency was added currently
    '''
    if dep_from == self.get_args('ppdep_from') and dep_to == self.get_args('ppdep_to') :
      return True
    else:
      return False

  def get_bool_arg(self, arg, default ):
    '''
      returns the value of the given arg, interpreted as bool (YES, NO, Y, N, TRUE, FALSE), caseinsensitve
    '''
    try:
      return { # switch/case in Python style
        'YES': True,
        'NO': False,
        'Y': True,
        'N': False,
        'TRUE': True,
        'FALSE': False,
        'T': True,
        'F': False,
      }.get( self.macrokw.get(arg).strip().upper(), default) # fallback: default
    except:
      return default

