/*
This is the js template for TracTweakUI plugin.
You should modify the selector part of following js code to meet your own trac environment.
*/

$(document).ready(function() {

	jQuery.extend(jQuery.validator.messages, {
			required: "必选字段",
			remote: "请修正该字段",
			email: "请输入正确格式的电子邮件",
			url: "请输入合法的网址",
			date: "请输入合法的日期",
			dateISO: "日期格式: 2008-12-31(如果格式已经正确, 请点击一次此输入框)",
			number: "请输入合法的数字",
			digits: "只能输入整数",
			creditcard: "请输入合法的信用卡号",
			equalTo: "请再次输入相同的值",
			accept: "请输入拥有合法后缀名的字符串",
			maxlength: jQuery.format("请输入一个长度最多是 {0} 的字符串"),
			minlength: jQuery.format("请输入一个长度最少是 {0} 的字符串"),
			rangelength: jQuery.format("请输入一个长度介于 {0} 和 {1} 之间的字符串"),
			range: jQuery.format("请输入一个介于 {0} 和 {1} 之间的值"),
			max: jQuery.format("请输入一个最大为 {0} 的值"),
			min: jQuery.format("请输入一个最小为 {0} 的值")
	});

	// validate
	$("#propertyform").validate();
	$("#field-plan_time_10").attr("class", "dateISO");
	$("#field-plan_time_11").attr("class", "dateISO");
	$("#field-plan_time_12").attr("class", "dateISO");

});