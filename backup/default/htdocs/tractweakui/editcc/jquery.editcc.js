/* Copyright (c) 2008 Richard Liao (richard.liao.i@gmail.com)
 * Dual licensed under the MIT (http://www.opensource.org/licenses/mit-license.php) 
 * and GPL (http://www.opensource.org/licenses/gpl-license.php) licenses.
 * Version 0.1
 */

;(function($) {

var editCcTarget;

$.fn.extend({
	editCc: function(options) {
		var editCcHtml = "<div id='list-cc' class='ac_results' style='display:none; position: absolute; '><table><tbody/></table></div>"
		var hoverHtml = "<a id='edit-cc' href='#' style='vertical-align:top;'>编辑</a>"

		$(editCcHtml).appendTo("body");
		return this.each(function() {
			$(this).after(hoverHtml);
			$(this).next().click(_onEditCc);
		});
	}
});


var _getUsers = function() {
	var cc = $(editCcTarget).val();
	var users = cc.split(",");
	var newUsers = [];
	for (i in users ) {
		newUser = users[i].replace(" ", "");
		if (users[i] && newUser) {
			newUsers.splice(newUsers.length, 0, newUser);
		}
	}
	return newUsers;
};

var _prepareListCc = function() {
	$("#list-cc table tbody").empty();

	var offset = $(editCcTarget).offset();
	var element = $("#list-cc");
	element.css({
		width: $(editCcTarget).width(),
		top: offset.top + editCcTarget.offsetHeight,
		left: offset.left
	});

	var users = _getUsers();
	if (users.length > 0) {
		for (i in users ) {
			$("#list-cc table tbody").append("<tr><td><a class='del-cc' id='del-cc-" + i + "' href='#'>" +"&nbsp;&nbsp;&nbsp;&nbsp;"+ "</a></td><td id='cc-" + i + "'>" + users[i] +"</td></tr>");
		}
		$("#list-cc a").bind("click", _onDelCc);
		$("#list-cc").show();
	} else {
		$("#list-cc").hide();
	}
};

var _onEditCc = function(evt) {
	editCcTarget = $(this).prev()[0];
	$(editCcTarget).click(_onExitEditCc);
	_prepareListCc();
	return false;
};

var _onDelCc = function(evt) {
	// update cc value
	var index = evt.target.getAttribute("id").substring(7,10);
	var users = _getUsers();
	users.splice(index, 1);

	var newCc = users.join(", ");
	if (newCc) {
		newCc = newCc + ", "
	}
	$(editCcTarget).val(newCc);

	// remove list cc
	$("#cc-" + index).parent().remove();

	// reset id of cc
	_prepareListCc();
	return false;
};

var _onExitEditCc = function(evt) {
	$("#list-cc").hide();
	return true;
};

})(jQuery);