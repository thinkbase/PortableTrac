jQuery(document).ready(function($) {
  $("#field-cc").autocomplete("../subjects", {
    multiple: true,
    formatItem: formatItem
  });
  $("input:text#field-reporter").autocomplete("../subjects", {
    formatItem: formatItem
  });
});