var workfloweditor;
if (!workfloweditor) workfloweditor = {};

/**
 * i18n
 */
workfloweditor.Localizer = function() {
    this.strings = {};
    this.lang = "";
    
    var htmlTag = document.getElementsByTagName("html")[0];
    this.lang = htmlTag.getAttribute("xml:lang") || htmlTag.getAttribute("lang");
    
    // If there isn't the lang attribute, use browser language.
    if (this.lang == null || this.lang == "") {
        var currentLanguage;
        if (navigator.browserLanguage) {
            currentLanguage = navigator.browserLanguage; 
        } else if (navigator.language) { 
            currentLanguage = navigator.language; 
        } else if (navigator.userLanguage) { 
            currentLanguage = navigator.userLanguage; 
        }
        
        if (currentLanguage && currentLanguage.length >= 2) {
            this.lang = currentLanguage.substr(0,2);
        }
    }
    
    var self = this;
    this.getLocalizedString = function(str) {
        if (!workfloweditor.Localizer.strings)
        {
            return str;
        }
        
        var message = workfloweditor.Localizer.strings[str];
        if (!message || message == "") {
            message = str;
        }
        return message;
    };
    
    return this;
}

workfloweditor.Localizer = new workfloweditor.Localizer();
_ = workfloweditor.Localizer.getLocalizedString;

/**
 * Workflow Editor onload action.
 */
jQuery(document).ready(function(){
    var context = new workfloweditor.WorkflowContext();
    
    // display grid
    context.updateModelByText("#workflowText");
    context.initGrid("#workflowGrid");
    context.initStatusGrid("#workflowStatusGrid");
    
    // display tab layout
    var tabsElem = $("#workflowTabs > ul").tabs();
    var currentTab = "gridTab";
    
    tabsElem.tabs("select", 0);
    tabsElem.bind("tabsselect", function(event, origEvent, ui) {
        currentTab = ui.panel.id;
        
        if (!ui.panel.id) {
            // do nothing
        } else if (ui.panel.id == "gridTab") {
            context.updateModelByText("#workflowText");
            context.refreshGrid();
        } else if (ui.panel.id == "textTab") {
            context.updateModelByGrid("#workflowGrid");
            context.refreshText();
        } else {
            // do nothing
        }
    });
    
    // Save button action
    // The workflow is updated before saving.
    jQuery("#doChanges").click( function() {
        try
        {
            if (currentTab == "textTab") {
            	currentTab = tabsElem.tabs().data('selected.tabs')
            	if (currentTab == "1") { 
                	context.updateModelByText("#workflowText");
                	context.refreshGrid();
                }
            }
            
            context.updateModelByGrid("#workflowGrid");
            context.refreshText();
        }
        catch(ex)
        {
            alert(_("Error: Please fix the workflow text.")
                  + "\n(error code = " + ex.number + ")");
            return false;
        }
    });
    
    $("#workflowTabs").show();
    
});

/**
 * Workflow Editor
 */
workfloweditor.WorkflowContext = function() {
    this.DEFAULT_OPERATIONS = {
                               ""                  : "",
                               "set_owner"         : _("set owner"),
                               "del_owner"         : _("del owner"),
                               "set_owner_to_self" : _("set owner to self"),
                               "set_resolution"    : _("set resolution"),
                               "del_resolution"    : _("del resolution"),
                               "leave_status"      : _("leave status")
                              };
    this.DEFAULT_PERMISSIONS = {
                                ""              : "",
                                "TICKET_VIEW"   : "TICKET_VIEW",
                                "TICKET_CREATE" : "TICKET_CREATE",
                                "TICKET_MODIFY" : "TICKET_MODIFY",
                                "TICKET_ADMIN"  : "TICKET_ADMIN"
                               };
    this.DEFAULT_STATUS = ["new", "assigned", "accepted", "reopened", "closed"];
    this.HIDDEN_COL     = ["operations", "permissions"];
    this.STATUS_PREFIX  = "status_";
    this.IMAGE_PATH     = "../../chrome/workfloweditor/images";
    this.EDIT_URL       = document.location + "/edit";
    
    this.model     = {};
    this.status    = [].concat(this.DEFAULT_STATUS);
    
    this.textId;
    this.gridId;
    this.statusGridId;
}

/**
 * The workflow text is converted to the workflow model.
 * 
 * @param textId  workflow textarea field ID
 */
workfloweditor.WorkflowContext.prototype.updateModelByText = function(textId) {
    this.textId = textId;
    
    var text = $(textId).val();
    if (!text) {
        return;
    }
    
    var lines = text.split("\n");
    var model = {};
    var status = this.status;
    for (var index = 0; index < lines.length; index++) {
        var line = lines[index];
        var pos = lines[index].indexOf("=");
        var param = jQuery.trim(line.substring(0, pos));
        var value = jQuery.trim(line.substring(pos + 1, line.length));
        
        // skip line
        if (!param || param.length <= 0) {
            continue;
        }
        
        // parse workflow text
        if (param.indexOf(".") < 0) {
            // parse action
            var action = param;
            var elems = value.split("->");
            var oldStatus = jQuery.trim(elems[0]);
            var newStatus = jQuery.trim(elems[1]);
            
            var workflow = model[action];
            if (!workflow) {
                workflow = {};
                model[action] = workflow;
            }
            workflow["action"]    = action;
            workflow["oldStatus"] = oldStatus;
            workflow["newStatus"] = newStatus;
            
            if ((newStatus != "*") && ($.inArray(newStatus, status) < 0)) {
                status.push(newStatus);
            }
        } else {
            // parse options
            var elems = param.split(".");
            var action    = elems[0];
            var attribute = elems[1];
            
            var workflow = model[action];
            if (!workflow) {
                workflow = {};
                model[action] = workflow;
            }
            workflow[attribute] = value;
        }
    }
    
    workfloweditor.WorkflowContext.normalizeModel(model);
    
    this.model  = model;
    this.status = status;
}

/**
 * The workflow grid data is converted to the workflow model.
 * 
 * @param gridId  workflow grid ID.
 */
workfloweditor.WorkflowContext.prototype.updateModelByGrid = function(gridId) {
    this.gridId = gridId;
    
    var dataIds = jQuery(gridId).getDataIDs();
    if (!dataIds || dataIds.length <= 0) {
        return;
    }
    
    var model = {};
    var status = this.status;
    var rowNum = dataIds.length;
    for (var index = 0; index < rowNum; index++) {
        var rowData = jQuery(gridId).getRowData(dataIds[index]);
        var action = rowData["action"];
        
        if (!action) {
            continue;
        }
        
        var oldStatus = [];
        for (col in rowData) {
            var pos = col.indexOf(this.STATUS_PREFIX);
            if ((pos == 0) && (rowData[col] == "Yes")) {
                var tempStatus = col.substring(this.STATUS_PREFIX.length, col.length);
                oldStatus.push(tempStatus);
            }
        }
        
        var defaultVal = rowNum - rowData["order"] + 1;
        if (defaultVal < 0) {
            defaultVal = 0;
        }
        
        var operations;
        for (ope in this.DEFAULT_OPERATIONS) {
            if (rowData["operations"] == this.DEFAULT_OPERATIONS[ope]) {
                operations = ope;
                break;
            }
        }
        
        var permissions;
        for (perm in this.DEFAULT_PERMISSIONS) {
            if (rowData["permissions"] == this.DEFAULT_PERMISSIONS[perm]) {
                permissions = perm;
                break;
            }
        }
        
        workflow = {};
        workflow["action"]      = action;
        workflow["oldStatus"]   = oldStatus.join(",");
        workflow["newStatus"]   = rowData["status"];
        workflow["name"]        = rowData["name"];
        workflow["default"]     = defaultVal;
        workflow["operations"]  = operations;
        workflow["permissions"] = permissions;
        
        model[action] = workflow;
        
        var newStatus = workflow["newStatus"];
        if ((newStatus != "*") && ($.inArray(newStatus, status) < 0)) {
            status.push(newStatus);
        }
    }
    
    workfloweditor.WorkflowContext.normalizeModel(model);
    
    this.model  = model;
    this.status = status;
}

/**
 * Normalize the workflow model.
 * 
 * @param model  workflow model 
 */
workfloweditor.WorkflowContext.normalizeModel = function(model) {
    for (var action in model) {
        var workflow = model[action];
        
        // set the default value.
        if (!workflow["name"]) {
            workflow["name"] = action;
        }
        if (!workflow["default"]) {
            workflow["default"] = 0;
        }
        if (!workflow["operations"]) {
            workflow["operations"] = "";
        }
        if (!workflow["permissions"]) {
            workflow["permissions"] = "";
        }
        
        var oldStatus = workflow["oldStatus"].split(",");
        for (var index = 0; index < oldStatus.length; index++) {
            var tempStatus = jQuery.trim(oldStatus[index]);
            oldStatus[index] = tempStatus;
        }
        workflow["oldStatus"] = oldStatus.join(",");
    }
}


/**
 * Refresh the grid.
 * If this method is called, the workflow model must be updated.
 */
workfloweditor.WorkflowContext.prototype.refreshGrid = function() {
    // remove the grid table and the grid edit layout.
    jQuery(this.gridId).GridUnload();
    jQuery("#editmod" + this.gridId.replace("#", "")).remove();
    
    this.initGrid(this.gridId);
}

/**
 * Refresh the text.
 * If this method is called, the workflow model must be updated.
 */
workfloweditor.WorkflowContext.prototype.refreshText = function() {
    var text = this.createWorkflowText();
    $(this.textId).val(text);
}


/**
 * Initialize the workflow grid.
 * 
 * @param gridId  grid element ID
 */
workfloweditor.WorkflowContext.prototype.initGrid = function(gridId) {
    var isFirst;
    if (!this.gridId) {
        isFirst = true;
    } else {
        isFirst = false;
    }
    
    this.gridId = gridId;
    
    var colNames   = this.createGridColNames();
    var colModel   = this.createGridColModel();
    
    jQuery(gridId).jqGrid({
        datatype    : "local",
        height      : 200,
        width       : 750,
        colNames    : colNames,
        colModel    : colModel,
        shrinkToFit : false,
        imgpath     : this.IMAGE_PATH,
        editurl     : this.EDIT_URL
    });
    
    var gridData = this.createGridData();
    for(var index = 0; index < gridData.length; index++) {
        jQuery(gridId).addRowData(index + 1, gridData[index]);
    }
    
    jQuery(gridId).sortGrid("order", false);
    
    if (isFirst) {
        var self = this;
        var showGridCol = function() {
            jQuery(gridId).showCol(self.HIDDEN_COL);
        }
        var hideGridCol = function() {
            $("#pData").hide();
            $("#nData").hide();
            jQuery(gridId).hideCol(self.HIDDEN_COL);
        }
        
        // add action setting
        $(gridId + "ItemAdd").click(function(){
            jQuery(gridId).editGridRow(
                "new",
                {
                 top               : 50,
                 left              : 200,
                 height            : 400,
                 width             : 300,
                 mtype             : "GET",
                 closeAfterAdd     : true,
                 reloadAfterSubmit : false,
                 beforeInitData    : showGridCol,
                 afterShowForm     : hideGridCol
                }
            );
        });
        
        // modify action setting
        $(gridId + "ItemMod").click(function(){
            var gr = jQuery(gridId).getGridParam("selrow");
            if( gr != null ) {
                jQuery(gridId).editGridRow(
                    gr,
                    {
                     top               : 50,
                     left              : 200,
                     height            : 400,
                     width             : 300,
                     mtype             : "GET",
                     closeAfterEdit    : true,
                     reloadAfterSubmit : false,
                     beforeInitData    : showGridCol,
                     afterShowForm     : hideGridCol
                    }
                );
            } else {
                alert(_("Please select row."));
            }
        });
        
        // delete action setting
        $(gridId + "ItemDel").click(function(){
            var gr = jQuery(gridId).getGridParam("selrow");
            if( gr != null ) {
                jQuery(gridId).delGridRow(
                    gr,
                    {
                     top               : 50,
                     left              : 200,
                     mtype             : "GET",
                     closeAfterEdit    : true,
                     reloadAfterSubmit : false
                    }
                );
            } else {
                alert(_("Please select row."));
            }
        });
        
    } // isFirst end
}

/**
 * Create the array of the grid column name.
 * 
 * @param colNames  the array of the grid column name
 */
workfloweditor.WorkflowContext.prototype.createGridColNames = function() {
    // for IE6
    // Localization function isn't initialized in the local function.
    if (!_) {
        _ = workfloweditor.Localizer.getLocalizedString;
    }
    
    var colNames = [_('action'), _('name'), _('operation'), _('permission'), _('order'), _('next status'), ''];
    colNames = colNames.concat(this.status);
    
    return colNames;
}

/**
 * Create the array of the grid column model.
 * 
 * @param colModel  the array of the grid column model
 */
workfloweditor.WorkflowContext.prototype.createGridColModel = function() {
    var statusValue = "*:*;";
    for (var index = 0; index < this.status.length; index++) {
        statusValue += this.status[index] + ":" + this.status[index] + ";";
    }
    statusValue = statusValue.substring(0, statusValue.length - 1);
    
    var opeValue = "";
    for (ope in this.DEFAULT_OPERATIONS) {
        opeValue += ope + ":" + this.DEFAULT_OPERATIONS[ope] + ";";
    }
    opeValue = opeValue.substring(0, opeValue.length - 1);
    
    var permValue = "";
    for (perm in this.DEFAULT_PERMISSIONS) {
        permValue += perm + ":" + this.DEFAULT_PERMISSIONS[perm] + ";";
    }
    permValue = permValue.substring(0, permValue.length - 1);
    
    var colModel = [
        {name:'action',      index:'action',      width:75,  editable:true,  editrules:{required:true, edithidden:false}},
        {name:'name',        index:'name',        width:100, editable:true,  editrules:{required:true}},
        {name:'operations',  index:'operations',  width:100, editable:true,  edittype:"select", editoptions:{value:opeValue},  hidden:true},
        {name:'permissions', index:'permissions', width:100, editable:true,  edittype:"select", editoptions:{value:permValue}, hidden:true},
        {name:'order',       index:'order',       width:45,  editable:true,  align:"right", sorttype:"int", editrules:{integer:true}},
        {name:'status',      index:'status',      width:100, editable:true,  edittype:"select", editoptions:{value:statusValue}},
        {name:'blank',       index:'blank',       width:22,  editable:false, align:"center"}
    ];
    
    for (var index = 0; index < this.status.length; index++) {
        var statusColModel = {
            name        : this.STATUS_PREFIX + this.status[index],
            index       : this.STATUS_PREFIX + this.status[index],
            width       : 75,
            editable    : true,
            align       : "center",
            edittype    : "checkbox",
            editoptions : {value:"Yes:No"}
        };
        
        colModel.push(statusColModel);
    }
    
    return colModel;
}

/**
 * Create the grid data from the workflow model.
 * 
 * @return grid data
 */
workfloweditor.WorkflowContext.prototype.createGridData = function() {
    var model  = this.model;
    var status = this.status;
    
    var modelSize = 0;
    for (var key in model) {
        modelSize++;
    }
    
    var gridData = [];
    for (var action in model) {
        var workflow = model[action];
        var rowData = {};
        
        var operations;
        if (this.DEFAULT_OPERATIONS[workflow["operations"]]) {
            operations = this.DEFAULT_OPERATIONS[workflow["operations"]];
        } else {
            operations = "";
        }
        
        var permissions;
        if (this.DEFAULT_PERMISSIONS[workflow["permissions"]]) {
            permissions = this.DEFAULT_PERMISSIONS[workflow["permissions"]];
        } else {
            permissions = "";
        }
        
        rowData["action"]      = workflow["action"];
        rowData["name"]        = workflow["name"];
        rowData["status"]      = workflow["newStatus"];
        rowData["operations"]  = operations;
        rowData["permissions"] = permissions;
        rowData["order"]       = modelSize - workflow["default"] + 1;
        rowData["blank"]       = "<--";
        
        var oldStatus = workflow["oldStatus"] + ",";
        for (var index = 0; index < status.length; index++) {
            var tempStatus = status[index];
            var match;
            if ((oldStatus == "*,") || (oldStatus.indexOf(tempStatus + ",") >= 0)) {
                match = "Yes";
            } else {
                match = "No";
            }
            rowData[this.STATUS_PREFIX + tempStatus] = match;
        }
        
        gridData.push(rowData);
    }
    
    return gridData;
}

/**
 * Initialize the status grid.
 * 
 * @param gridId  status grid element ID
 */
workfloweditor.WorkflowContext.prototype.initStatusGrid = function(statusGridId) {
    var isFirst;
    if (!this.statusGridId) {
        isFirst = true;
    } else {
        isFirst = false;
    }
    
    this.statusGridId = statusGridId;
    
    jQuery(statusGridId).hide();
    
    jQuery(statusGridId).jqGrid({
        datatype    : "local",
        height      : 0,
        width       : 0,
        colNames    : [_("status")],
        colModel    : [{
                        name:'editableStatus', index:'status', width:100, editable:true,
                        edittype:"textarea", editrules:{required:true}, editoptions: {rows:"10",cols:"15"},
                        hidden:true
                      }],
        imgpath     : this.IMAGE_PATH,
        editurl     : this.EDIT_URL,
        loadui      : "disable"
    });
    
    jQuery(statusGridId).addRowData(1, {editableStatus : this.status.join(" ")});
    
    if (isFirst) {
        var self = this;
        var showGridCol = function() {
            jQuery(statusGridId).showCol(["editableStatus"]);
        }
        var dataSplit = function() {
            $("#pData").hide();
            $("#nData").hide();
            var statusValue = $("#editableStatus").val();
            statusValue = statusValue.replace(/ /g, "\n");
            $("#editableStatus").val(statusValue);
            jQuery(statusGridId).hideCol(["editableStatus"]);
        }
        var updateStatus = function() {
            var statusValue = $("#editableStatus").val();
            var statusArray = statusValue.split("\n");
            
            // update status
            self.status = [];
            for (var index = 0; index < statusArray.length; index++) {
                var tempStatus = jQuery.trim(statusArray[index]);
                if (tempStatus.length > 0) {
                    self.status.push(tempStatus);
                }
            }
            
            self.updateModelByGrid(self.gridId);
            self.refreshGrid();
        }
        
        // modify action setting
        $(statusGridId + "ItemMod").click(function(){
            jQuery(statusGridId).editGridRow(
                1,
                {
                 top               : 50,
                 left              : 200,
                 height            : 250,
                 width             : 350,
                 mtype             : "GET",
                 closeAfterEdit    : true,
                 reloadAfterSubmit : false,
                 beforeInitData    : showGridCol,
                 afterShowForm     : dataSplit,
                 onclickSubmit     : updateStatus
                }
            );
        });
    
    } // isFirst end
}

/**
 * Create the workflow text from the workflow model.
 */
workfloweditor.WorkflowContext.prototype.createWorkflowText = function() {
    
    var textArray = [];
    for (var action in this.model) {
        
        var workflow = this.model[action];
        
        if (!workflow) {
            continue;
        }
        
        var operations = workflow["operations"];
        var permissions = workflow["permissions"];
        
        // create each workflow define.
        textArray.push(action + " = " + workflow["oldStatus"] + " -> " + workflow["newStatus"]);
        textArray.push(action + ".name = " + workflow["name"]);
        textArray.push(action + ".default = " + workflow["default"]);
        if (operations && operations.length > 0) {
            textArray.push(action + ".operations = " + operations);
        }
        if (permissions && permissions.length > 0) {
            textArray.push(action + ".permissions = " + permissions);
        }
    }
    
    var text = textArray.join("\n");
    return text;
}

