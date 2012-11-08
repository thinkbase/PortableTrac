# -*- coding: utf-8 -*-

import re
import os
import os.path
import stat
import shutil
import datetime

from genshi.builder import tag

from trac.core import *
from trac.resource import *
from trac.attachment import Attachment
from trac.prefs.api import IPreferencePanelProvider
from trac.web import IRequestHandler
from trac.web.chrome import ITemplateProvider, add_stylesheet, add_script
from trac.mimeview.api import get_mimetype
from trac.ticket.query import *
from trac.ticket.model import Ticket
from trac.admin.api import *
from trac.perm import *

from ppfilter import *
from pptickets import *
from pprender import *
from ppenv import *
from ppticketviewtweak import *
from ppticketdatetweak import *
from ppcreatedependingtickettweak import *
from pputil import *

from pkg_resources import resource_filename

class PPConfigAdminPanel(Component):
    implements(IAdminPanelProvider)

    def get_admin_panels(self,req):
      """Return a list of available admin panels.

      The items returned by this function must be tuples of the form
      `(category, category_label, page, page_label)`.
      """
      if 'TRAC_ADMIN' in req.perm:
        yield( 'ProjectPlanConfig', 'ProjectPlan', 'General', 'General Settings' )
        yield( 'ProjectPlanConfig', 'ProjectPlan', 'Color', 'Color Settings' )
        yield( 'ProjectPlanConfig', 'ProjectPlan', 'Image', 'Image Settings' )

    def render_admin_panel(self, req, category, page, path_info):
      """Process a request for an admin panel.

      This function should return a tuple of the form `(template, data)`,
      where `template` is the name of the template to use and `data` is the
      data to be passed to the template.
      """
      req.perm.require( 'TRAC_ADMIN' )

      macroenv = PPEnv( self.env, req, '' )

      if req.method == 'POST':
        # ! evertime the configuration changes, wipe the Cache completly, since
        # most of the options change the rendering
        sexcept = ""
        try:
          macroenv.cache.wipe()
          self.env.log.info('cache %s wiped' % macroenv.cache.root )
        except Exception, e:
          self.env.log.exception(e)
        for k in macroenv.conf.flatconf.keys():
          if req.args.has_key( 'flat_' + k ):
            macroenv.conf.set( k, req.args[ 'flat_' + k ] )
        for ( k, optl ) in macroenv.conf.listconf.items():
          for subk in macroenv.conf.get_map( k ).keys():
            if req.args.has_key( 'list_' + k + '_' + subk ):
              macroenv.conf.set_map_val( k, subk, req.args[ 'list_' + k + '_' + subk ] )
        macroenv.conf.save()
        req.redirect( req.href.admin( category, page ) )

      if category == 'ProjectPlanConfig':
        # TODO: add style via css file to page
        #add_stylesheet( formatter.req, 'projectplan/js/jquery-tooltip/jquery.tooltip.css' )
        confdict = self.__getconfdict( req, macroenv.conf, page )
        iconset = {}
        iconset['icons'] = sorted(PPImages.selectable('none' , self.env).keys())
        #iconset['icons'].sort()
        iconset['chromebase'] = req.href.chrome( 'projectplan', PPConstant.RelDocPath )
        data = { 'confdict': confdict,
                 'page': page, 
                 'iconset': iconset }
        return 'admin_ppconf.html',data
      else:
        raise TracError( "Unknown Category: %s" % category )

    def __getconfdict( self, req, conf, page ):
      confdict = {}
      # load flatconf with groupid and catid if existend
      for ( k, opt ) in conf.flatconf.items():
        if opt.groupid and opt.catid == page:
          if opt.groupid not in confdict:
            confdict[ opt.groupid ] = {}
          opttype = 'text'
          sellist = []
          chromebase = ''
          if isinstance( opt, PPSingleSelOption ):
            opttype = 'selectable'
            if isinstance( opt, PPImageSelOption ):
              opttype = 'selectable_image'
              chromebase = req.href.chrome( 'projectplan', opt.RelDocPath )
            s = opt.selectable()
            if isinstance( s, dict ):
              sellist = s.keys()
            elif isinstance( s, list ):
              sellist = s
            else:
              opttype = 'text'
              self.env.log.warning( 'Selectable for %s must be list or dict for html based selections, ignored.' % opt.key )
          confdict[ opt.groupid ][ opt.key ] = { 'opttype': opttype,
                                                 'val': conf.get( k ),
                                                 'id': 'flat_' + k,
                                                 'doc': opt.doc }
          if ( opttype=='selectable' ) or ( opttype=='selectable_image' ):
            confdict[ opt.groupid ][ opt.key ]['sellist'] = sellist
            if opttype=='selectable_image':
              confdict[ opt.groupid ][ opt.key ]['chromebase'] = chromebase

      # load listconf
      for ( k, optl ) in conf.listconf.items():
        if optl.groupid and optl.catid == page:
          opttype = 'text'
          sellist = []
          if isinstance( optl, PPListOfSelOptions ):
            opttype = 'selectable'
            if isinstance( optl, PPListOfImageSelOptions ):
              opttype = 'selectable_image'
              chromebase = req.href.chrome( 'projectplan', optl.selector().RelDocPath )
            s = optl.selector().selectable()
            if isinstance( s, dict ):
              sellist = s.keys()
            elif isinstance( s, list ):
              sellist = s
            else:
              opttype = 'text'
              self.env.log.warning( 'Selectable for %s must be list or dict for html based selections, ignored.' % optl.key )
          if optl.groupid not in confdict:
            confdict[ optl.groupid ] = {}
          for ( subk, subv ) in conf.get_map( k ).items():
            confdict[ optl.groupid ][ subk ] = { 'opttype': opttype,
                                                 'val': subv,
                                                 'doc': optl.doc % subk,
                                                 'id': 'list_' + k + '_' + subk }
            if ( opttype=='selectable' ) or ( opttype=='selectable_image' ):
              confdict[ optl.groupid ][ subk ]['sellist'] = sellist
              if opttype=='selectable_image':
                confdict[ optl.groupid ][ subk ]['chromebase'] = chromebase

      return confdict

class PPCacheContentProvider(Component):
    implements(IRequestHandler)

    # IRequestHandler methods
    def match_request( self, req ):
      '''
        match basicly everything, check later for existence
      '''
      return re.match( '/'+ PPConstant.cache_content_suffix + '/(.*)$', req.path_info )

    def process_request( self, req ):
      '''
        serve the request but check wether the file realy is in cache
        ( absolute second part, f.e. an attemp to access restricted areas )
        for those request, trying access files anywhere, serve an Exception,
        otherwise let it handle send_file, which checks for existence and serves
        either the file or an error
      '''
      if req.path_info.startswith('/'):
        slashes = 2
      else:
        slashes = 1
      name = req.path_info[(slashes+len(PPConstant.cache_content_suffix)):]
      # dont use the cache, just verify the file existence and
      conf = PPConfiguration( self.env )
      cpath = os.path.normpath( conf.get( 'cachepath' ) )
      fname = os.path.normpath( name )
      if os.path.isabs( fname ):
        self.env.log.warn( 'Attempted bypass ( access for %s ) ' %fname )
        raise TracError( 'Access Denied for "%s"' % fname )
      accessname = os.path.join( cpath, name )
      # no isfile and exitence check, both are done on send_file with error handling
      return req.send_file( accessname, get_mimetype( accessname ) )


class PPChangeTicketProvider(Component):
    implements(IRequestHandler)
    '''
      handler enables to save ticket changes via for example ajax calls 
    '''

    # IRequestHandler methods
    def match_request( self, req ):
      '''
        match basicly everything, check later for existence
      '''
      return re.match( '/'+ PPConstant.change_ticket_suffix + '/(.*)$', req.path_info )

    def process_request( self, req ):
      '''
        serve the request but check wether the file realy is in cache
        ( absolute second part, f.e. an attemp to access restricted areas )
        for those request, trying access files anywhere, serve an Exception,
        otherwise let let it handle send_file, which checks for existence and serves
        either the file or an error
      '''
      path = PPHTDPathSelOption.absbasepath()
      if req.path_info.startswith('/'):
        slashes = 2
      else:
        slashes = 1
      name = req.path_info[(slashes+len(PPConstant.change_ticket_suffix)):]
      self.conf = PPConfiguration( self.env )
      self.req = req

      done = self.update_connections()
      if done:
        name = 'crystal_project/16x16/state/ok.png'
        accessname = os.path.join( path, name )
      else:
        #name = 'images/crystal_project/16x16/messagebox/critical.png'
        raise TracError( 'Ticket Save Fail: %s --> %s ' % (self.get_args('ppdep_from'), self.get_args('ppdep_to') ) )

      return req.send_file( accessname, get_mimetype( accessname ) )

    def get_args( self , argname):
      '''
        get http url parameter
      '''
      try:
        return self.req.args.get( argname )
      except:
        return None


    def update_connections(self):
      '''
        Rewrite Ticket Dependencies
      '''
      # search choosen connection of tickets
      dep_from = self.get_args('ppdep_from')
      dep_to = self.get_args('ppdep_to')

      # 1. check for numbers
      if dep_from == None or dep_to == None or (
           not dep_from.strip().isdigit() ) or (
           not dep_to.strip().isdigit() ):
        return False

      dep_from = dep_from.strip()
      dep_to = dep_to.strip()

      # 2. check for valid tkid
      if ( not Ticket.id_is_valid( dep_from ) ) or (
           not Ticket.id_is_valid( dep_to ) ):
        return False

      toticket = Ticket( self.env, int(dep_to) )
      # 3. check valid ticket from database
      if toticket.id == None:
        return False

      # get dependencies
      depstring = toticket.get_value_or_default( 
        self.conf.get( 'custom_dependency_field' ) )
      if depstring != None:
        deps = pputil.ticketIDsFromString( depstring )
      else:
        deps = set()

      # modify dependencies
      if int(dep_from) in deps:
        comstring = "removed dependency #%s" % str(dep_from)
        deps.remove( int(dep_from) )
      else:
        comstring = "added dependency #%s" % str(dep_from)
        deps.add( int(dep_from) )

      # build new depstring
      depstring = ",".join( [ str(d) for d in deps ] )
      toticket[ self.conf.get( 'custom_dependency_field' ) ] = depstring

      # commit
      try:
        if not toticket.save_changes( self.req.authname, comstring ):
          raise TracError( "Could not update Ticket #%s " % str(dep_to) )
      except:
        return False

      return True



class ProjectPlanMacro(WikiMacroBase):
    '''
      Project Plan Macro
    '''
    implements(ITemplateProvider)

    def get_templates_dirs( self ):
      return [ resource_filename( __name__, 'templates' ) ]

    def get_htdocs_dirs( self ):
      return [ ( 'projectplan', resource_filename( __name__, 'htdocs' ) ) ]

    def expand_macro( self, formatter, name, content ):
        '''
          Wiki Macro Method which generates a Genshi Markup Stream
        '''
        macrostart = datetime.now()
        
        addExternFiles( formatter.req )
        # needed because of ajax call while showing ticket details
        add_stylesheet( formatter.req, 'common/css/ticket.css' )
        
        if content == None:
          content = ''
        macroenv = PPEnv( self.env, formatter.req, content )
        ts = ppFilter( macroenv ).get_tickets()
        
        if macroenv.get_args('ppforcereload') == '1':
          noteForceReload = tag.span('The visualization was recreated.', class_ = 'ppforcereloadinfo' )
        else:
          noteForceReload = tag.span()
        
        renderer = ppRender( macroenv )
        
        # show text in the headline
        moretitle = ''
        #macroenv.tracenv.log.warning('macroenv label=%s (%s)' % (macroenv.get_args('label'),macroenv.tracreq.args))
        if macroenv.macrokw.get('label', None) != None: # use parameter: label 
          moretitle = macroenv.macrokw.get('label', '')
        else:
          moretitle = renderer.getHeadline() # get the pre-defined headline
          
        
	  
        
        return tag.div(
                 tag.h5( tag.a( name=macroenv.macroid )( '%s' % (moretitle,)  ) ),
                 renderer.render( ts ),
                 tag.div(  
                         tag.div( 
			    tag.span('It took '+str((datetime.now()-macrostart).microseconds/1000)+'ms to generate this visualization. ' , class_ = 'ppstat' ),
			    noteForceReload,
			    tag.span(tag.a('Force recreation of the visualization.', href='?ppforcereload=1', class_ = 'ppforcereload' ) )
			    )
                         ),
                 style=macroenv.macrokw.get('style', '') # CSS style
                 )
                 #tag.div( id = 'ppstat' ) )


