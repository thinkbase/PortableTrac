# -*- coding: utf-8 -*-

from trac.core import *
from trac.resource import *
from genshi.builder import tag
from genshi.core import TEXT
from genshi.filters import Transformer
from genshi.input import HTML
from trac.ticket.api import ITicketManipulator
from trac.web.api import ITemplateStreamFilter, IRequestFilter #, IRequestHandler
from trac.ticket.model import Ticket
from trac.ticket.query import *
from ppenv import PPConfiguration
from pputil import *
import re

class PPTicketViewTweak(Component):
  '''
    BETA: computes links on ticket dependency entries
  '''
  implements(ITemplateStreamFilter, IRequestFilter)
  
  field = None
  fieldrev = None

  def lazy_init( self ):
    self.field = PPConfiguration( self.env ).get('custom_dependency_field')
    self.fieldrev = PPConfiguration( self.env ).get('custom_reverse_dependency_field')

  # ITemplateStreamFilter methods
  def filter_stream(self, req, method, filename, stream, data):  
    '''
      replace the dependency-field by links
    '''
    
    # stop if this is not a ticket view
    if not req.path_info.startswith('/ticket/') and not req.path_info.startswith('/newticket'):
      return stream
    
    self.lazy_init()
    
    current_ticket_id = None
    try:
      current_ticket_id = str(data['ticket'].id)
      dependencies = self.getDependsOn(current_ticket_id)
      #dependencies = '1, 8; 2 y 3, 99,x' # test
    except Exception,e:
      #self.env.log.debug('filter_stream fail '+repr(e))
      return stream
    
    deptickets = self.splitStringToTicketList(dependencies)
    dependencies = self.createNormalizedTicketString( deptickets ) # normalized
    
    blocked_tickets = self.getBlockedTickets( current_ticket_id ) 
    blocked_tickets_string = self.createNormalizedTicketString(blocked_tickets)
    
    nodeptickets = [ t for t in deptickets if str(t).strip() != "" and not isNumber(t) ]
    actualdeptickets = [ t for t in deptickets if str(t).strip() != "" and isNumber(t) ]
    
    depwithlinks = self.getTicketLinkList(req, actualdeptickets, nodeptickets)
    blocked_tickets_with_links = self.getTicketLinkList(req, blocked_tickets, [])
    
    self.env.log.debug('nodeptickets of '+str(current_ticket_id)+': '+repr(nodeptickets))
    self.env.log.debug('actualdeptickets of '+str(current_ticket_id)+': '+repr(actualdeptickets))
    self.env.log.debug('dependencies of '+str(current_ticket_id)+': '+repr(dependencies))
    
    # change summary block
    if str(depwithlinks) != '': # change HTML only if there is actually a link to show
      stream |= Transformer('//*[@headers="h_%s"]/text()' % self.field).replace(depwithlinks)
   
    if str(blocked_tickets_with_links) != '':
      stream |= Transformer('//*[@headers="h_%s"]/text()' % self.fieldrev).replace( blocked_tickets_with_links )
    
    # change fields
    stream |= Transformer('//*[@id="field-%s"]' % (self.field)).attr('value', dependencies)
    stream |= Transformer('//*[@id="field-%s"]' % (self.fieldrev)).attr('value', blocked_tickets_string)  
    # create a backup field containing the earlier value
    stream |= Transformer('//*[@id="propertyform"]').prepend( tag.input(name='field_%s_backup' % (self.fieldrev), value=blocked_tickets_string, style='display:none') )
    
    
    
    # publish data that should be used by javascript
    stream |= Transformer('body/div[@id="main"]').prepend(
      tag.div( 
        tag.div( req.environ.get( 'ticketclosedf' ), id='ppDateFormat'),
        tag.div( 'field-'+self.field, id='ppDependenciesField'),
        tag.div( 'field-'+self.fieldrev, id='ppDependenciesReverseField'),
        id='ppTicketViewTweakConf'
    ))
    
    return stream
 
 
  # IRequestFilter methods
  def pre_process_request(self, req, handler):
    
    def createDiff( ticket_id ):
      '''
        HACK: need an indicator when the ticket was created lately
      '''
      diff = -1
      if ticket_id != None:
        created = Ticket(self.env, int(ticket_id)).time_created
        now = datetime.now(created.tzinfo) # needs tzinfo!
        created = datetime.combine( created.date(), created.time() )
        now = datetime.combine( now.date(), now.time() )
        diff = now - created
        diff = diff.seconds + diff.days * 24 * 3600 # calculated here, to be compatible to python <2.7
      return diff
    
    
    if req.path_info.startswith('/ticket/') or req.path_info.startswith('/newticket'):
      self.lazy_init()
      
      # get blocked tickets and save the dependencies
      blocked_tickets = req.args.get('field_'+self.fieldrev)
      blocked_tickets_backup = req.args.get('field_%s_backup' % (self.fieldrev) )
      ticket_id = req.args.get('id')
      
      # if the ticket was created lately, the blocking-dependencies are only available within ticket attribute; they are now added to the blocked tickets
      #self.env.log.error("\n\n")
      #self.env.log.error('pre_process_request: #%s  %s  %s' % (ticket_id,req.path_info, repr(req.args)))
      #self.env.log.error('pre_process_request: #%s  %s  %s' % (ticket_id,req.path_info, req.args.get('submit') ))
      #self.env.log.error('pre_process_request: #%s  %s  %s' % (ticket_id,'blocked_field', blocked_tickets ))
      
      newTicketFlag = False
      if (0 <= createDiff( ticket_id ) <= 1) and req.path_info.startswith('/ticket') :
        blocked_tickets = Ticket(self.env, int(ticket_id)).get_value_or_default(self.fieldrev) # read from the DB
        self.env.log.warning('pre_process_request: new ticket #%s created: %s --> save blocked tickets' % (ticket_id, blocked_tickets)) # hack
        newTicketFlag = True
      
      # save "blocks tickets": save if the field was provided and changed, moreover, the submit button was hit 
      if (blocked_tickets != None and (blocked_tickets != blocked_tickets_backup) and req.path_info.startswith('/ticket') and req.args.get('submit') != "" and req.args.get('submit') != None) or newTicketFlag:
        self.authname = req.authname
        #blocked_tickets = Ticket(self.env, int(ticket_id)).get_value_or_default(self.fieldrev)
        self.change_blocked_tickets( ticket_id , blocked_tickets )
      
      
      #if blocked_tickets != None :
      self.authname = req.authname
      
    return handler

  def post_process_request(self, req, template, data, content_type):
    '''
      add javascript and stylesheet to ticket view
    '''
    if req.path_info.startswith('/ticket/') or req.path_info.startswith('/newticket'):
      addExternFiles(req)
    
    return template, data, content_type

  def getBlockedTickets(self, ticket_id):
    '''
      calculate blocking tickets of the given ticket
      returns list of ticket ids (as string)
    '''
    sqlconstraint = '0'
    #sqlconstraint += " OR value = \"%s\"" % (ticket_id,) # lonely value
    #sqlconstraint += " OR value LIKE \"%% %s %%\"" % (ticket_id,) # middle
    #sqlconstraint += " OR value LIKE \"%% %s\"" % (ticket_id,) # left 
    #sqlconstraint += " OR value LIKE \"%s %%\"" % (ticket_id,) # right
    
    # TODO precondition: normalize dependencies field
    sqlconstraint += " OR value = \"%s\"" % (ticket_id,) # lonely value
    sqlconstraint += " OR value LIKE \"%% %s,%%\"" % (ticket_id,) # middle
    sqlconstraint += " OR value LIKE \"%% %s\"" % (ticket_id,) # left 
    sqlconstraint += " OR value LIKE \"%s,%%\"" % (ticket_id,) # right
    
    #sqlconstraint += " OR value = \"#%s\"" % (ticket_id,) # lonely value
    #sqlconstraint += " OR value LIKE \"%% #%s %%\"" % (ticket_id,) # middle
    #sqlconstraint += " OR value LIKE \"%%,%s\"" % (ticket_id,) # left 
    #sqlconstraint += " OR value LIKE \"%s,%%\"" % (ticket_id,) # right
    
    # LIMIT for safety reasons
    sql = "SELECT ticket FROM ticket_custom WHERE name = \"%s\" AND ( %s ) LIMIT 0,250" % (self.field, sqlconstraint )
    self.env.log.debug("getBlockedTickets: SQL: " + repr(sql))
    db = self.env.get_db_cnx()
    cursor = db.cursor()
    cursor.execute(sql)
    blocking_tickets = cursor.fetchall()
    ret = []
    for res in blocking_tickets:
      ret.append(str(res[0]))
    
    return ret
  
  def splitStringToTicketList( self, tickets, current_ticket_id = -1 ):
    r = re.compile('[;, ]')
    if tickets == None:
      return []
    else:
      tickets = r.split(tickets)
      tickets = [ t.replace('#', '')  for t in tickets ]
      tickets = [ t for t in tickets if str(t).strip() != "" and t != current_ticket_id ]
      return list(set(tickets))

  def getDependsOn( self, ticket_id ):
    self.env.log.debug('getDependsOn of #'+str(ticket_id)+': '+ repr(Ticket(self.env, int(ticket_id)).get_value_or_default(self.field).replace(ticket_id, "")))
    return Ticket(self.env, int(ticket_id)).get_value_or_default(self.field).replace(ticket_id, "")

  def getTicketLinkList(self, req, deptickets, nodeptickets):
    '''
      translate ticket list into a div structure with ticket links
    '''
    ticketsasstring = (','.join(deptickets))
    tickets = Query( self.env, constraints={ 'id' : [ticketsasstring] } ).execute( req )
    depwithlinks = ''
    sep = ''
    for dep in deptickets:
      if depwithlinks != '':
        sep = ', '
      else:
        sep = ''
      cssclass='ticket '
      try:
        ticket = [ t for t in tickets if str(t['id']) == dep ].pop()
        cssclass += ticket['status']+' ticket_inner' # need ticket_inner for mouseover effect
        # TODO: replace by absolute link
        depwithlinks = tag.span(depwithlinks, sep, tag.a( '#' + dep, href="./"+dep, class_ = cssclass ) )
      except Exception, e:
        cssclass += 'unknownticket'
        depwithlinks = tag.span(depwithlinks, sep, tag.a( '#' + dep , title="unknown ticket", class_ = cssclass) )
      
    cssclass = 'unknownticket'
    for nodep in nodeptickets :
      depwithlinks = tag.span(depwithlinks, sep, tag.a( nodep , title="no ticket id", class_ = cssclass) )
      sep = ', '
    
    return depwithlinks

  def createNormalizedTicketString( self, ticketlist ):
    '''
      remove all false entries in the list of tickets
    '''
    ticketstr = ', '.join([ t.strip().replace('#', '') for t in ticketlist  if str(t).strip() != "" ])
    return ticketstr

  def change_blocked_tickets( self , ticket_id, saved_blocked_tickets ):
    
    if ticket_id == None:
      return
    
    self.env.log.warning('change_blocked_tickets: #%s saved_blocking_tickets: %s' % (ticket_id, saved_blocked_tickets) )
    
    # tickets saved in the form
    saved_blocked_tickets = self.splitStringToTicketList( saved_blocked_tickets )
    # tickets currently saved in the database
    stored_blocked_tickets = self.getBlockedTickets( ticket_id )
    
    saved_blocked_tickets.sort()
    stored_blocked_tickets.sort()
    #self.env.log.debug('change_blocked_tickets: #'+ticket_id+' saved_blocking_tickets: '+repr(saved_blocked_tickets ) )
    #self.env.log.debug('change_blocked_tickets: #'+ticket_id+' stored_blocking_tickets: '+repr(stored_blocked_tickets) )
    
    for blocked_ticket_id in saved_blocked_tickets :
      if blocked_ticket_id in stored_blocked_tickets: # change nothing 
        self.env.log.debug('NO new blocked ticket: #'+ticket_id+': %s was in %s' % (blocked_ticket_id,stored_blocked_tickets))
        pass
      elif not blocked_ticket_id in stored_blocked_tickets: # new blocking ticket id
        self.env.log.debug('ADD: new blocked ticket id '+blocked_ticket_id+' at #'+str(ticket_id))
        self.addBlockedTicket(ticket_id, blocked_ticket_id)
    
    for tid in stored_blocked_tickets:
      if tid in saved_blocked_tickets : # change nothing 
        self.env.log.debug('NO new blocked ticket: #%s already in %s' % (tid,saved_blocked_tickets) )
        pass
      else: 
        self.env.log.debug('REMOVE '+str(ticket_id)+' from former blocked ticket id '+str(tid) )
        self.removeBlockedTicket(ticket_id, tid)

  def addBlockedTicket( self, ticket_id, blocked_ticket_id ):
    '''
      add ticket_id to dependencies of blocked_ticket_id
    '''
    try:
      blocked_ticket_depends_on_tickets = self.getDependsOn(blocked_ticket_id)
      blocked_ticket_depends_on_ticket_list = self.splitStringToTicketList(blocked_ticket_depends_on_tickets)
      if not ticket_id in blocked_ticket_depends_on_ticket_list:
        blocked_ticket_depends_on_ticket_list.append(str(ticket_id))
        newvalue = self.createNormalizedTicketString(blocked_ticket_depends_on_ticket_list)
        self.env.log.debug('add: save to '+blocked_ticket_id+': '+repr(blocked_ticket_depends_on_tickets)+' --> '+repr(newvalue))
        
        self.saveDependenciesToDatabase( blocked_ticket_id, newvalue )
        Ticket(self.env, blocked_ticket_id).save_changes(self.authname, 'note: change "'+blocked_ticket_depends_on_tickets+'" to "'+newvalue+'" (add '+ticket_id+') initiated by #'+str(ticket_id)) # add comment to ticket
       
      else:
        self.env.log.debug('not added: '+blocked_ticket_id+': '+repr(blocked_ticket_depends_on_tickets) )
    except Exception,e:
      self.env.log.error('ticket #%s error while adding a blocked ticket: %s' % ( ticket_id, repr(e) ) )
    

  def removeBlockedTicket( self, ticket_id, old_blockedtid):
    '''
      remove ticket_id from the dependencies of old_blockedtid
    '''
    dependencies = self.getDependsOn(old_blockedtid)
    dependencies_list = self.splitStringToTicketList(dependencies)
    new_dependencies_list = [ t.strip() for t in dependencies_list if str(t).strip() != ticket_id ]
    new_dependencies = self.createNormalizedTicketString(new_dependencies_list)
    
    self.saveDependenciesToDatabase( old_blockedtid, new_dependencies )
    comment = 'note: change "'+dependencies+'" to "'+new_dependencies+'" (remove '+str(ticket_id)+') initiated by #'+str(ticket_id) 
    try:
      Ticket(self.env, old_blockedtid).save_changes(self.authname, comment ) # add comment to ticket
      self.env.log.error('consider #%s: change dependencies of #%s: %s --> %s' % (ticket_id, old_blockedtid, dependencies, new_dependencies) )
    except Exception,e:
      self.env.log.error('error while adding the comment "%s" to #%s: %s' % (comment,ticket_id,repr(e)) )

  def saveDependenciesToDatabase( self, ticket_id, newvalue):
    '''
      save new value to ticket custom
    '''
    sql = "UPDATE ticket_custom SET value = \"%s\" WHERE ticket = \"%s\" AND name = \"%s\" " % (newvalue, ticket_id, self.field )
    db = self.env.get_db_cnx()
    cursor = db.cursor()
    cursor.execute(sql)
    db.commit()
