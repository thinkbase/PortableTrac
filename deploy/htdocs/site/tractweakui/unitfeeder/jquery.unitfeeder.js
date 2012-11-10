/* Copyright (c) 2008 Richard Liao (richard.liao.i@gmail.com)
 * Dual licensed under the MIT (http://www.opensource.org/licenses/mit-license.php) 
 * and GPL (http://www.opensource.org/licenses/gpl-license.php) licenses.
 * Version 0.1
 */

;(function($) {

$.fn.extend({

	unitFeeder: function(options) {
		var unitHtml = "<select></select>";
		return this.each(function(index) {
			var unitWrapper = $(unitHtml);
			$(this).after(unitWrapper);
			for (i in options.units){
				$(unitWrapper).append("<option>"+ options.units[i] +"</option>");
			}
			
			$(this).next().change(_onUnitSelected);
		});
	}
});

var _onUnitSelected = function(evt) {
	var feedTarget = $(this).prev()[0];
	var curVal = $(feedTarget).val();

	var newVal = curVal;
	var result = curVal.match(/\d+/g);
	if (result) {
		newVal = result[0] + $(this).val();
	}

	$(feedTarget).val(newVal);
	return false;
};

})(jQuery);