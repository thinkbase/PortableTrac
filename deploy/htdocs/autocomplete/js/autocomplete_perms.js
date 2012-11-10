$(document).ready(function() {
  $("#gp_subject").autocomplete("../../subjects?groups=1", {
    formatItem: formatItem
  });
  $("#sg_subject").autocomplete("../../subjects?groups=1", {
    formatItem: formatItem
  });
  $("#sg_group").autocomplete("../../subjects?groups=1&users=0", {
    formatItem: formatItem
  });
});
