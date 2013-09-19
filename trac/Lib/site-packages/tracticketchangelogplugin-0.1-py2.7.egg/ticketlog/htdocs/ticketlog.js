$(document).ready(function() {
    // 获取Trac根URL
    var base_url = $("#search").attr("action").replace(/\/search$/g, "");

    var onQueryError = function(msg){
        error_html = "<table class='listing'><tbody><tr style='background-color: yellow;'><td>Error in querying changelogs.</td><tr></tbody></table>";
        $("#ticket").after(error_html);
    };
    
    var onQuerySuccess = function(result){
        if (!result.data || !result.data.revisions.length) {
            return;
        }

        var ticket_id = result.data.ticket_id;
        var headers = result.data.headers;
        var header_width = result.data.header_width;
        var revisions = result.data.revisions;

        var table_html = "<h2 id='ticket_revisions_head' style='cursor:pointer; background: url(../chrome/common/expanded.png) no-repeat 0px 50%; padding-left: 16px;'>Changelogs</h2><table id='ticket_revisions' class='listing'><tbody><tr>";
        for (var i=0; i<headers.length; i++) {
            var header = headers[i];
            var width = header_width[i];
            
            var th = "<th style='width: "+width+"'>"+header+"</th>";
            table_html += th;
        }
        table_html += "<tr></tbody></table>";

        $("#ticket_revisions").append(tr_html);

        $("#ticket").after(table_html);

        // 生成表格
        for (var i=0; i<revisions.length; i++) {
            var revision = revisions[i];
            var tr_html = "<tr><td><a target='_blank' href='../changeset/"+revision.link+"'>["+revision.rev+"]</a></td><td>"+revision.author+"</td><td>"+revision.time+"</td><td>"+revision.message+"</td></tr>";
            $("#ticket_revisions").append(tr_html);
        }
        
        // 处理折叠展开
        $("#ticket_revisions_head").click(function(){
            $("#ticket_revisions").toggle();
            if ($("#ticket_revisions:visible").length) {
                $("#ticket_revisions_head").css("background-image", "url(../chrome/common/expanded.png)");
            } else {
                $("#ticket_revisions_head").css("background-image", "url(../chrome/common/collapsed.png)");
            }
        });
    };

    var ticket_id = location.pathname.replace(base_url + "/ticket/", "");

    var data = {
        "ticket_id": ticket_id
    };

    $.ajax({
        type: 'POST',
        url: base_url + "/ticketlog/query",
        data: JSON.stringify(data),
        contentType: "application/json",
        cache: false,
        async: false,
        dataType: 'json',
        success: onQuerySuccess,
        error: onQueryError
    });
});
