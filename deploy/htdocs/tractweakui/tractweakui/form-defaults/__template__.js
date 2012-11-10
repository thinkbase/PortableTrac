/*
This is the js template for TracTweakUI plugin.
You should modify the selector part of following js code to meet your own trac environment.
*/

$(document).ready(function() {

	$("#field-memo").DefaultValue("附加信息...");
	$("#field-deploy_number_10").DefaultValue("格式: 部门_产品_语言_版本_类型_日期_序号");
	$("#field-operator_10").DefaultValue("例如: 张三 zhangsan@kingsoft.com");
	$("#field-reason_10").DefaultValue("描述部署的内容...");
	$("#field-other_10").DefaultValue("文件大小等信息...");
	$("#field-scan_file_10").DefaultValue("扫描文件svn地址...");

	$("#field-receiver_11").DefaultValue("例如发布给王小二, 读权限就仅限于他...");
	$("#field-privelege_11").DefaultValue("上传, 只读下载, 列表浏览等等...");
	$("#field-reason_11").DefaultValue("描述申请的内容...");
	$("#field-other_11").DefaultValue("可选其他信息...");

	$("#field-pack_size_12").DefaultValue("数据包大小...");
	$("#field-user_num_12").DefaultValue("预计用户数量...");
	$("#field-reason_12").DefaultValue("描述申请的内容...");
	$("#field-other_12").DefaultValue("可选其他信息...");

});