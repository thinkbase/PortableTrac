/**
 * AnBo
 * beta
 * adds java script date picker to tickets
 */

/**
 * datum darstellen
 */
function ppShowDatePicker(moreID , fieldid)
{
	if( document.getElementById("ppDatePickerDiv"+moreID) ){
	 var datePicker = 	document.getElementById("ppDatePickerDiv"+moreID);
	} else {
	  var datePicker = 	document.createElement("div");
		  datePicker.id = "ppDatePickerDiv"+moreID;
		  datePicker.setAttribute('style','position:absolute; display:none;');
		  datePicker.innerHTML = '';
	  document.body.appendChild(datePicker);
	}
	now = new Date();
	var monat = now.getMonth();

	ppInitDatePicker(datePicker, monat, fieldid );
	
}

var ppCurrentTimeSegment = new Array();
var ppWeeks = 5;

// still buggy, while filling the table data
function ppInitDatePicker(datePickerDiv, monat, fieldid)
{
	if( document.getElementById(fieldid) )
	{

	}
	else
	{
		return;
	}
	today = new Date();

	now = new Date();
	oneday = 24*60*60 * 1000; // sec
	lastvalue = document.getElementById(fieldid).value;

	timeshift = ppCurrentTimeSegment[fieldid] * oneday * 7 * ppWeeks; // shift time forward/backward
	now.setTime(now.getTime() + timeshift - (7*oneday)); // eine Woche weniger

// 	alert('pp: start: '+ppCurrentTimeSegment[fieldid]+"\n"+now);
	// search for a monday
	while( now.getDay() != 1 )
	{
		now.setTime(now.getTime() - oneday);
	}	

	css = '';
	tmp = '';
	tmp += '<table id="ppDatePicker" border="0" cellpadding="0" cellspacing="0">';
	tmp += '<tr>';
	tmp += '<th '+css+'>Mo</th>';
	tmp += '<th '+css+'>Tu</th>';
	tmp += '<th '+css+'>We</th>';
	tmp += '<th '+css+'>Th</th>';
	tmp += '<th '+css+'>Fr</th>';
	tmp += '<th '+css+'>Sa</th>';
	tmp += '<th '+css+'>Su</th>';
	tmp += '</tr>';

	var i;
	var rowcounter = 0;
	for( i=0; i<(ppWeeks*7) ; i++ ) // 5 weeks
	{
		newdate = new Date();
		newdate.setTime((i*oneday)+now.getTime()); 
		
		if( rowcounter % 2 == 0) {
		  trclass = 'odd'
		} else {
		  trclass = 'even'
		}

		if( (i % 7)  == 0 )
		{
			tmp += '<tr class="'+trclass+'">';
		}

		myday = newdate.getDate();
		if( myday < 10 ) myday = '0'+myday;
		mymonth = (newdate.getMonth()+1);
		if( mymonth < 10 ) mymonth = '0'+mymonth;
		mydate = myday+'/'+mymonth+'/'+newdate.getFullYear(); 

		css = '';
		if( (i % 7 ) == 5 ){
			css += ' saturday ';
		}
		if( (i % 7 ) == 6 ){
			css += ' sunday ';
		}
		if( lastvalue == mydate ) { //  currently selected date
			css += ' selecteddate ';
		}
		if( newdate.getTime() == today.getTime() ) { // today
			css += ' today ';
		}

		tmp += '<td class="'+css+'" align="right" onclick="document.getElementById(\''+fieldid+'\').value = \''+mydate+'\';">'+newdate.getDate()+'.'+mymonth+'.</td>';

		if( (i % 7) == 6)
		{
			tmp += '</tr>';
		}
		
		rowcounter++;

	} // for
	
	prevbutton = '<input class="ppButtonLeft" type="button" onclick="ppRedrawCalendar(\''+datePickerDiv.id+'\', -1, \''+fieldid+'\');" value="&lsaquo;&lsaquo;" title="previous weeks">';
	closebutton = '<input  class="ppButton" type="button" onclick="ppCloseCalendar(\''+datePickerDiv.id+'\');" value="close">';
	resetbutton = '<input  class="ppButton" type="button" onclick="document.getElementById(\''+fieldid+'\').value = \''+lastvalue+'\';" value="original value">';
	nextbutton = '<input  class="ppButtonRight" type="button" onclick="ppRedrawCalendar(\''+datePickerDiv.id+'\', 1, \''+fieldid+'\');" value="&rsaquo;&rsaquo;" title="next weeks">';

	tmp += '<tfoot><tr><td colspan="7">'+prevbutton+' &nbsp; '+resetbutton+' &nbsp; '+closebutton+' &nbsp; '+nextbutton+'</td></tr></tfoot>';

	tmp  += '</table>';
	/*
	$('#textbox').live('keydown', function(e) { 
	  var keyCode = e.keyCode || e.which; 
	  if (keyCode == 9) { 
	    e.preventDefault(); 
	    // call custom function here
	  } 
	});
	*/
//  	alert('x3 '+tmp);
	datePickerDiv.innerHTML = tmp;
}

function ppRedrawCalendar(divId, addSegment, fieldid){
  ppCloseCalendar(divId);
  ppCurrentTimeSegment[fieldid] += addSegment;
  ppShowDatePicker(fieldid, fieldid);
  document.getElementById('ppDatePickerDiv'+fieldid).style.display = 'block';
}


function ppCloseCalendar( divId) {
  document.getElementById(divId).style.display = 'none';
}


function saveDate( fieldid, date )
{
}


function ppCreateDatePickerInitActions(inputFieldId, ppDatePickerDiv )
{
	    $('#'+inputFieldId).focus(function(){
	      $('#'+ppDatePickerDiv).fadeIn(200,function(){});
	      positionDivByElement( document.getElementById(inputFieldId), document.getElementById(ppDatePickerDiv), 1 ); // TODO: replace with jquery
	    });
	    
	    $('#'+inputFieldId).keydown( function(event){
	      if (event.which == 9 || event.which == 27) { // TAB or ESC
		$('#'+ppDatePickerDiv).fadeOut(200,function(){});
	      }
	    });
}

function ppCreateDatePicker()
{
	if( document.getElementById('ppShowDatePicker') ) {
	    if( document.getElementById('field-due_assign') && document.getElementById('field-due_close'))
	    {
		    ppCurrentTimeSegment['field-due_assign'] = 0;
		    ppCurrentTimeSegment['field-due_close'] = 0;
		    ppShowDatePicker('field-due_assign', 'field-due_assign');
		    ppShowDatePicker('field-due_close', 'field-due_close');
	    }
	    else
	    {
		    return;
	    }

	    ppCreateDatePickerInitActions('field-due_assign', 'ppDatePickerDivfield-due_assign');
	    ppCreateDatePickerInitActions('field-due_close', 'ppDatePickerDivfield-due_close');
	} else {
// 	  alert('not loaded');
	}
}

/********************************************************
Position the dropdown div below the input text field., abgewandelt von http://gadgetopia.com/autosuggest/
********************************************************/
function positionDivByElement(/* base */ el , /* move this */ div, mode)
{
	if( mode == 1 ) // drunter
	{
		var x = 0;
		var y = el.offsetHeight;
	}
	else // neben
	{
		var x = el.offsetWidth;
		var y = 0;
	}

	//Walk up the DOM and add up all of the offset positions.
	while (el.offsetParent && el.tagName.toUpperCase() != 'BODY')
	{
		x += el.offsetLeft;
		y += el.offsetTop;
		el = el.offsetParent;
	}

	x += el.offsetLeft;
	y += el.offsetTop;

	div.style.left = x + 'px';
	div.style.top = y + 'px';
};



$(document).ready(function () {
	ppCreateDatePicker();
});




