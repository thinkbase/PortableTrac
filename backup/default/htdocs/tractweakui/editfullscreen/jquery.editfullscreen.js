/* Copyright (c) 2008 Richard Liao (richard.liao.i@gmail.com)
 * Dual licensed under the MIT (http://www.opensource.org/licenses/mit-license.php) 
 * and GPL (http://www.opensource.org/licenses/gpl-license.php) licenses.
 * Version 0.1
 */

;(function($) {

var efsTarget;

$.fn.extend({

	editFullScreen: function() {
		var efsIframeHtml = "<div id='efs_container'> <div style='width:100%;border-bottom:solid 2px;'><a id='efs_save' href='#'>保存</a>&nbsp;<a id='efs_cancel' href='#'>取消</a></div> <div id='efs_div' style='width:100%; height:100%; border:none; padding:0; margin:0;'><textarea style='width:99%;height:100%;border:none;'><div> </div>";
		var hoverHtml = "<a href='#'>编辑</a>";

		$(efsIframeHtml).appendTo("body");
		
		$("#efs_save").click(_onSaveEfs);
		$("#efs_cancel").click(_onCancelEfs);

		_hideEfs();

		return this.each(function() {
			$(this).after(hoverHtml);
			$(this).next().click(_onEditFullScreen);
		});
	}
});

var _onEditFullScreen = function(evt) {
	efsTarget = $(this).prev()[0];
	var fullScreenStyle = { 'z-index': '100',
							'border': 'none',
							'position': 'absolute',
							'width': '100%',
							'height': '1000px',
							'top': '0',
							'left': '0',
							'background-color': 'white'
						};
	var efs_body = $("#efs_div textarea");
	efs_body.val($(efsTarget).val());
	efs_body.autogrow({ minHeight:100, 
						maxHeight:100000, 
						lineHeight:16
		});
		
	$('body > div').not("#efs_container").hide();
	$("#efs_container").css(fullScreenStyle).show();
};

var _hideEfs = function() {
	var normalStyle =     { 'z-index': '-100',
							'border': 'none',
							'position': 'absolute',
							'width': '0',
							'height': '0',
							'top': '0',
							'left': '0',
							'background-color': 'white'
						};
	$("#efs_container").css(normalStyle).hide();
	$('body > div').not("#efs_container").show();
};

var _onSaveEfs = function(evt) {
	_hideEfs();
	$(efsTarget).val($('textarea', $("#efs_div")).val());
	return false;
};

var _onCancelEfs = function(evt) {
	_hideEfs();
	return false;
};

})(jQuery);