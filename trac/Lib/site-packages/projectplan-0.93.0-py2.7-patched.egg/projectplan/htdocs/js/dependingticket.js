/**
 * AnBo, beta
 * ticket: adds javascript link looking like a button allowing to create a depending ticket
 * newticket: adds given ticket number to dependencies field
 */

/**
 * add button
 */
function ppCreateNewDependingTicket()
{
  if( /\/ticket\//.test(window.location.href) ) {
    var ppCreateNewDependingTicket = '<div style="margin-top:1.5ex;float:left"><a href="#" name="ppCreateNewDependingTicket" style="background-color:#EEE; padding: 0.1em 0.5em; border: 1px outset #CCCCCC; color:#222; margin:1em 0.5em 0.1em 0;" onclick="return ppCreateNewDependingTicketAction(this);">Create new depending ticket</a></div>';
    var ppCreateNewBlockingTicket = '<div style="margin-top:1.5ex;float:left"><a href="#" name="ppCreateNewBlockingTicket" style="background-color:#EEE; padding: 0.1em 0.5em; border: 1px outset #CCCCCC; color:#222; margin:1em 0.5em 0.1em 0;" onclick="return ppCreateNewBlockingTicketAction(this);">Create new blocking ticket</a></div>';
    $('.buttons').append('<div>'+ppCreateNewDependingTicket+ppCreateNewBlockingTicket+'</div>');
  }
}

/**
 * add dependencies ticket to new ticket form
 */
function ppAddDependenciesToNewDependingTicket()
{
  if( /\/newticket/.test(window.location.href) ) {
  pos = window.location.search.search(/\?dep=/);
    if( pos > -1 ) {
      $('#field-dependencies').val(window.location.search.substr(pos+('?dep='.length)));
    }
  pos = window.location.search.search(/\?blocking=/);
    if( pos > -1 ) {
      $('#field-dependenciesreverse').val(window.location.search.substr(pos+('?blocking='.length)));
    }
  }
}

/**
 * new form action
 */
function ppCreateNewDependingTicketAction(mylink) {
  mylink.href = window.location.href.replace(/\/ticket\//, '/newticket?dep=' );
  return true;
}
function ppCreateNewBlockingTicketAction(mylink) {
  mylink.href = window.location.href.replace(/\/ticket\//, '/newticket?blocking=' );
  return true;
}
 


$(document).ready(function () {
	ppCreateNewDependingTicket();
	ppAddDependenciesToNewDependingTicket();
});




