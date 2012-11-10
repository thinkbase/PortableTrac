/*
This is the js template for TracTweakUI plugin.
You should modify the selector part of following js code to meet your own trac environment.
*/

$(document).ready(function() {
	// field notice
	$("input[@id='field-need_authorize_10']").fieldNotice("二进制文件改变需要万里签字");
	$("input[@id='field-need_deploy_10']").fieldNotice("<div style='color:#ff0000;font-size:12px'>注意: 文件大于2M, 不能使用自动发布功能.</div>");
	$("input[@id='field-deploy_number_10']").fieldNotice("例: DUBA_KXE_CHS_V7_INS_080901_1");
	$("input[@id='field-operator_10']").fieldNotice("例: 张三 zhangsan@kingsoft.com");
	$("input[@id='field-scan_file_10']").fieldNotice("例: http://svn.rdev.kingsoft.net/KSSOP/tasks/deploy/2008/1.pdf");
	$("input[@id='field-summary']").fieldNotice("<a href='http://wiki.rdev.kingsoft.net/moin/OpWorkflowTutorial'>使用教程</a> &nbsp; <a href='http://wiki.rdev.kingsoft.net/moin/OpWorkflow'>流程说明</a> &nbsp; <a href='http://demo.rdev.kingsoft.net/kssop/wiki/TracTicketsValues'>传票字段详解</a> &nbsp; 注意: 请在传票中按规定使用<a href='http://wiki.rdev.kingsoft.net/moin/OpKeyWords'>关键字</a>");

	$("label[@for='field-description']").parents('tr').remove();
	//$("tr:has(#field-keywords)").remove();

});