$(document).ready(function(){
    $('.select_code').click(
        function (e) {
            var a = $('#code' + $(this).attr('id')).get(0);
			// Not IE
			if (window.getSelection) {
				var s = window.getSelection();
				// Safari
				if (s.setBaseAndExtent)	{
					s.setBaseAndExtent(a, 0, a, a.innerText.length - 1);
				} else { // Firefox and Opera
					var r = document.createRange();
					r.selectNodeContents(a);
					s.removeAllRanges();
					s.addRange(r);
				}
			} else if (document.getSelection) { // Some older browsers
				var s = document.getSelection();
				var r = document.createRange();
				r.selectNodeContents(a);
				s.removeAllRanges();
				s.addRange(r);
			} else if (document.selection) { // IE
				var r = document.body.createTextRange();
				r.moveToElementText(a);
				r.select();
			}
			e.stopImmediatePropagation();
        }
    );
    $('a').click(
        function(e) {
            e.stopImmediatePropagation();
        }
    );
    $('.title').not($('.title').children()).click(
        function () {
            $(this).next('.code').slideToggle();
            $(this).toggleClass('collapsed');
        }
    );
});
