$(document).ready(function() {
    // get base URL
    var base_url = $("#search").attr("action").replace(/\/search$/g, "");

    var not_number = function(s) {
        return isNaN(parseInt(s));
    };

    var onQueryError = function() {
        // prompt error message
        $("#content").prepend("<div id='query_error_msg' style='display: none; border: solid 1px; background-color: yellow;'>Right in place edit start failed.</div>");
        $("#query_error_msg").fadeIn("fast").fadeTo(5000, 1).fadeOut("slow", function(){
            $("#query_error_msg").remove();
        });
    };

    var onQuerySuccess = function(result) {
        var field_infos = result.field_infos;

        // each cell
        $("div#content table.tickets td[class]").hover(function(){
            var cell = $(this);
            var href = cell.parent().find("td.ticket a, td.id a").attr("href");
            if (!href || href.length<1) {
                return;
            }
            var parts = href.split("/");
            var ticket_id = parts[parts.length-1];
            if (not_number(ticket_id)) {
                return;
            }

            var field_name = cell.attr("class");
            if (field_name.length<1) {
                return;
            }

            if (!(field_name in field_infos)) {
                return;
            }


            // clone field_info
            var field_info = JSON.parse(JSON.stringify(field_infos[field_name]));


            var field_value = $.trim(cell.text());
            if (field_info['type'] == "select") {
                if (!(field_value in field_info['options'])) {
                    // add current value to options
                    field_info['options'][field_value] = field_value;
                }
                // selected
                if (field_info['options'][field_value] == field_value) {
                    field_info['options']["selected"] = field_value;
                }
            }

            var onSaveSubmit = function(settings, original) {
                var old_value = settings.submitdata['old_value'];
                var cur_value = $("form input, form select", original).val();
                if (old_value == cur_value) {
                    // reset
                    $(original).html(original.revert);
                    original.editing   = false;
                    // prevent from submit
                    return false;
                }
                // continue submit
                return true;
            };

            var onSaveError = function(settings, original, xhr) {
                // reset
                $(original).html(original.revert);
                original.editing   = false;
                $(original).css("background-color", "#e06060");
            };

            var onSaveSuccess = function(original, settings) {
                $(this).css("background-color", "#60c070");
                // update settings
                settings.submitdata['old_value'] = $.trim(cell.text());

                var field_name = settings.submitdata['field'];
                field_info = JSON.parse(JSON.stringify(field_infos[field_name]));
                if (field_info['type'] == "select") {
                    settings.data = field_info['options'];
                    settings.data["selected"] = $.trim(cell.text());
                }
            };

            // jeditable
            cell.editable(base_url+"/ripe/save", {
                type        :  field_info['type'],
                data        :  field_info['options'],
                submit      : 'OK',
                id          : 'id',
                name        : 'value',
                style       : 'inherit',
                width       : 'none',
                select      : true,
                placeholder : '',
                indicator   : '<img src="'+base_url+'/chrome/ripe/indicator.gif">',
                submitdata  : {"ticket_id": ticket_id, "field": field_name, "old_value": field_value},
                ajaxoptions : {
                    type        : 'GET'
                },
                onsubmit    : onSaveSubmit,
                callback    : onSaveSuccess,
                onerror     : onSaveError,
                tooltip     : 'Edit'
            });

        });
    };

    // query fields info
    $.ajax({
        type: 'GET',
        url: base_url+'/ripe/query',
        data: {},
        cache: false,
        async: false,
        dataType: 'json',
        success: onQuerySuccess,
        error: onQueryError
    });
});

