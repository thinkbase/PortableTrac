(function($){
	$.fn.addEditlink = function(title){
		var cnt = 1;
		var title = title || "Edit this section";
		var href_edit = document.location.href;
		href_edit = (href_edit.indexOf('?')==-1?'?':href_edit+'&')+"action=edit&section=";
		return this.filter("*[@id]").each(function(){
			$("<a class='anchor'>[<span>edit</span>]</a>").attr("href", href_edit + cnt++).attr("title", title).appendTo(this);
		});
	}
	
	$(document).ready(function() {
		 $("#wikipage >:header").addEditlink("Edit this section");
	});
})(jQuery);
