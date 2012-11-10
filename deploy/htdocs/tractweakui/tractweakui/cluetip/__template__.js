/*
This is the js template for TracTweakUI plugin.
You should modify the selector part of following js code to meet your own trac environment.
*/

$(document).ready(function() {
	$("#field-memo").attr("title", "附加信息");
	$("#field-other_10, #field-other_11, #field-other_12").attr("title", "可选其他信息");
	$("#field-reason_10, #field-reason_11, #field-reason_12").attr("title", "描述申请的内容");
	$("#field-memo").cluetip();
	$("#field-other_10, #field-other_11, #field-other_12").cluetip();
	$("#field-reason_10, #field-reason_11, #field-reason_12").cluetip();
});