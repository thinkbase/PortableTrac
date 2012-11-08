/*
This is the js template for TracTweakUI plugin.
You should modify the selector part of following js code to meet your own trac environment.
*/

$(document).ready(function() {
	// unit feeder
	var unitOptions = {
			units:['B', 'KB', 'MB', 'GB']
		}
	$("#field-pack_size_12").unitFeeder(unitOptions);

	var unitOptions = {
			units:['个', '万', '亿']
		}
	$("#field-user_num_12").unitFeeder(unitOptions);

});