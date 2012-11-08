Raphael.fn.drawGrid = function (x, y, w, h, wv, hv, color) {
    yBase = Math.round( Math.log(hv) / Math.log(10) );
    yStep = Math.pow( 10,  yBase - 1); 
    if ( yStep < 1 ) {
      yStep = 1;
    }
    yStart = hv % yStep;
    color = color || "#000";
    var path = ["M", x, y, "L", x + w, y, x + w, y + h, x, y + h, x, y],
        rowHeight = h / hv,
        columnWidth = w / wv;
    for (var i = yStart; i < hv; i = i + yStep ) {
        path = path.concat(["M", x, y + i * rowHeight, "L", x + w, y + i * rowHeight]);
    }
    for (var i = 1; i < wv; i = i + 1 ) {
        path = path.concat(["M", x + i * columnWidth, y, "L", x + i * columnWidth, y + h]);
    }
    return this.path(path.join(",")).attr({stroke: color});
};

window.onload = function () {
  $(".ppConfBurnDown").each(function () {
	ppDrawBurndown("#"+this.id);
  });
}

function ppDrawBurndown(dataId){
    // Grab the data
    var labels = [],
	labelsAxis = [],
        data = [],
		finished = [],
		reopened = [],
		dataX = [],
		maxTickets = parseInt($(dataId+" .maxTasks").html()),
		maxLength = parseInt($(dataId+" .maxlength").html());

     $(dataId+" .data thead th").each(function () {
         labels.push($(this).html());
     });
     $(dataId+" .data tfoot  th").each(function () {
          labelsAxis.push($(this).html());
     });
     $(dataId+" .data tbody :nth-child(1) td").each(function () {
         data.push($(this).html());
     });
     $(dataId+" .data tbody :nth-child(2) td").each(function () {
         finished.push($(this).html());
     });
     $(dataId+" .data tbody :nth-child(3) td").each(function () {
         reopened.push($(this).html());
     });

    // Draw
    var         
	colorhue = .6 || Math.random(),
        color = "hsb(" + [colorhue, 1, .75] + ")",
        colorFinished = "#BF0000", // darkred
        colorLeft = color,
        colorPerfect = "hsb(" + [.24, 1, .75] + ")",
        colorToday = "hsb(" + [.24, 1, .75] + ")",
        colorBox = "#EEE",
        colorBoxBorder = "#999", // "#474747",
        colorGrid = "#999",
        borderX = 50, // px space at the right side
        borderY = 50, // px space at the bottom line
        tOffset = 10, // the higher, the closer is the text to x-axis
	widthFrame = parseInt($(dataId+" .width").html()),
        heightFrame = parseInt($(dataId+" .height").html()),
	width = widthFrame - borderX,
	height = heightFrame - borderY,
        today = parseInt($(dataId+" .today").html()),
        label1 = $(dataId+" .label1").html(),
        label2 = $(dataId+" .label2").html(),
 	heightTooltip = 50,
	widthTooltip = 115,
	offsetTooltip = 20,
	max = Math.max.apply(Math, data),
        xgrid = labels.length-1,
        ygrid = max,
	xWidth = 10,
	rightOffsetTooltip = widthTooltip/5,
        leftgutter = widthTooltip/2,
        bottomgutter = 20,
        topgutter = heightTooltip+offsetTooltip,
        r = Raphael($(dataId+" .holder").html(), widthFrame, heightFrame),
        txtAxis = {font: '10px Verdana, Arial', fill: "#000"},
        txtDate = {font: '12px Verdana, Arial', fill: "#000"},
        txtLeft = {font: '10px Verdana, Arial', fill: colorLeft },
        txtFinished = {font: '10px Verdana, Arial', fill: colorFinished },
        txt = {font: '12px Verdana, Arial', fill: "#fff"},
        txt1 = {font: '10px Verdana, Arial', fill: "#fff"},
        txt2 = {font: '12px Verdana, Arial', fill: "#000"},
        X = (width - leftgutter) / labels.length,
        Y = (height - bottomgutter - topgutter) / max,
        dotSize = 5;
	strokeLineWidth = 2;

	var perfectLine = [];
    for (var i = 0, ii = labels.length; i < ii; i++) {
	  perfectLine.push(max - (max/(labels.length-1) * i));
    }

    r.drawGrid(leftgutter + X * .5, topgutter, width - leftgutter - X, height - topgutter - bottomgutter, xgrid, ygrid, colorGrid);
    
    widthTooltip = Math.round(widthTooltip / 18 * maxLength ) // extend the width of the info box if more text is inserted
    var
	pathPerfectFuture = r.path().attr({stroke: colorPerfect, opacity: .75, "stroke-width": strokeLineWidth, "stroke-dasharray": "." }),
	pathPerfect = r.path().attr({stroke: colorPerfect, "stroke-width": strokeLineWidth }),
	path = r.path().attr({stroke: color, "stroke-width": 4, "stroke-linejoin": "round"}),
	bgp = r.path().attr({stroke: "none", opacity: .3, fill: color}).moveTo(leftgutter + X * .5, height - bottomgutter),
	frame = r.rect(10, 10, widthTooltip, heightTooltip, 5).attr({fill: colorBox, stroke: colorBoxBorder, "stroke-width": 2, opacity: .85 }).hide(), // label
        label = [],
        is_label_visible = false,
        leave_timer,
        blanket = r.set(),
        xLastBgp = -1,
	yLastPerfect = -1;
        
    label[0] = r.text(60, 10, "date").attr(txtDate).hide();
    label[1] = r.text(60, 40, "label1").attr(txtLeft).hide();
    label[2] = r.text(60, 70, "label2").attr(txtFinished).hide();

    for (var i = 0, ii = labels.length; i < ii; i++) {
        var
	    y = Math.round(height - bottomgutter - Y * data[i]),
	    yFinished = Math.round(height - bottomgutter - Y * finished[i]),
	    yPerfect = Math.round(height - bottomgutter - Y * perfectLine[i]),
	    // rotate the text at the x-axis
            x = Math.round(leftgutter + X * (i + .5)),
            t = r.text(x, height , labelsAxis[i]).attr(txtAxis).toBack().rotate(0); // x axis
            t2 = r.text(x - Math.round(t.getBBox().width / 2) , height - tOffset , labelsAxis[i]).attr(txtAxis).toBack().rotate(-45, x, height - tOffset); // x axis
            t.remove();
            
		if( i <= today ) {
		  var dot = r.circle(x, y, dotSize).attr({fill: color, stroke: "#000"}); // size of bullet 
		  bgp[i == 0 ? "lineTo" : "cplineTo"](x, y, 10); // filled area
		  pathPerfect[i == 0 ? "moveTo" : "cplineTo"](x, yPerfect, 0); // stroke line
		  path[i == 0 ? "moveTo" : "cplineTo"](x, y, 10); // stroke line
		  if( i == today ) {
		    pathPerfect["cplineTo"](x, height - bottomgutter, 0); // stroke line
		    xLastBgp = x;
		    yLastPerfect = yPerfect;
		  }
		} else {
		  dotSize = 0;
		  var dot = r.circle(x, y, dotSize).attr({fill: color, stroke: "#000"}); // invisible bullet, might be used later
		}


        blanket.push(r.rect(leftgutter + X * i, 0, X, height - bottomgutter).attr({stroke: "none", fill: "#fff", opacity: 0}));

	// bar with finished tickets
        var rect = blanket[blanket.length - 1];
		r.rect(x-(xWidth/2), yFinished, xWidth, height-yFinished-bottomgutter).attr({fill: colorFinished}); // number of finished tickets
		



        (function (x, y, data, lbl, lbl2, dot, dotSize) {
            var timer, i = 0;
	    if (dotSize == 0) { return; }
			// label
            $(rect.node).hover(function () {
                clearTimeout(leave_timer);
                var newcoord = {x: x - (widthTooltip/2), y: y - heightTooltip - offsetTooltip};
                if (newcoord.x + widthTooltip > width) {
                     newcoord.x -= rightOffsetTooltip; // for some reason a small offset is needed
                }
                frame.show().animate({x: newcoord.x, y: newcoord.y}, 200 * is_label_visible);
                label[0].attr({text: lbl  +"             "}).show().animateWith(frame, // + ((data % 10 == 1) ? "" : "s")
						{x: +newcoord.x + (widthTooltip/2), y: +newcoord.y + 12}, 200 * is_label_visible);
                label[1].attr({text: label1 + data }).show().animateWith(frame,
						{x: +newcoord.x + (widthTooltip/2), y: +newcoord.y + 27}, 200 * is_label_visible);
                label[2].attr({text: label2 + lbl2 }).show().animateWith(frame,
						{x: +newcoord.x + (widthTooltip/2), y: +newcoord.y + 40}, 200 * is_label_visible).attr();
                dot.attr("r", dotSize*1.5);
                is_label_visible = true;
            } , function () { // show/hide label 
                dot.attr("r", dotSize);
                leave_timer = setTimeout(function () {
                    frame.hide();
                    label[0].hide();
                    label[1].hide();
                    label[2].hide();
                    is_label_visible = false;
                    // r.safari();
                }, 1);
            });
        })(x, y, data[i], labels[i], finished[i], dot, dotSize);
    }

    // capture the scenario, where the time span is in the past
    if ( xLastBgp == -1 ) {
      xLastBgp = x;
      yLastPerfect = height - bottomgutter; // baseline
    }      
      
    // finish lines 
    bgp.lineTo(xLastBgp, height - bottomgutter).andClose();
    pathPerfectFuture["moveTo"](xLastBgp, yLastPerfect, 0); // stroke line
    pathPerfectFuture["cplineTo"](x, height - bottomgutter, 0); // stroke line
    
    
    frame.toFront();
    label[0].toFront();
    label[1].toFront();
    label[2].toFront();
    blanket.toFront();
};