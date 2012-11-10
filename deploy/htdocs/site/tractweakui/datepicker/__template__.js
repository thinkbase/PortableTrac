/*
This is the js template for TracTweakUI plugin.
You should modify the selector part of following js code to meet your own trac environment.
*/

$(document).ready(function() {
	Date.dayNames = ['日', '一', '二', '三', '四', '五', '六'];
	Date.abbrDayNames = ['日', '一', '二', '三', '四', '五', '六'];
	Date.monthNames = ['一月', '二月', '三月', '四月', '五月', '六月', '七月', '八月', '九月', '十月', '十－月', '十二月'];
	Date.abbrMonthNames = ['一月', '二月', '三月', '四月', '五月', '六月', '七月', '八月', '九月', '十月', '十－月', '十二月'];
	Date.firstDayOfWeek = 7;
	Date.format = 'yyyy-mm-dd';

	$.dpText = {
		TEXT_PREV_YEAR		:	'上一年',
		TEXT_PREV_MONTH		:	'上一月',
		TEXT_NEXT_YEAR		:	'下一年',
		TEXT_NEXT_MONTH		:	'下一月',
		TEXT_CLOSE			:	'关闭',
		TEXT_CHOOSE_DATE	:	'&nbsp;&nbsp;&nbsp;&nbsp;'
	}

	$("#field-plan_time_10").datePicker({startDate:'1970-01-01'});
	$("#field-plan_time_11").datePicker({startDate:'1970-01-01'});
	$("#field-plan_time_12").datePicker({startDate:'1970-01-01'});

});