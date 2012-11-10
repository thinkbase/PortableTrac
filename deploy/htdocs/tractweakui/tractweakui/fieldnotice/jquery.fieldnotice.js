/* Copyright (c) 2008 Richard Liao (richard.liao.i@gmail.com)
 * Dual licensed under the MIT (http://www.opensource.org/licenses/mit-license.php) 
 * and GPL (http://www.opensource.org/licenses/gpl-license.php) licenses.
 * Version 0.1
 */

;(function($) {

$.fn.extend({

	fieldNotice: function(notice) {
		var noticeHtml = "<br/><small><em><div style='font-size: 12px;'>" + notice + "</div></em></small>";
		return this.each(function(index) {
			$(this).wrap("<span>").after($(noticeHtml));
		});
	}
});

})(jQuery);