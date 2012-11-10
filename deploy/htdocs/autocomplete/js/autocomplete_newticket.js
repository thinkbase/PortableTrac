jQuery(document).ready(function($) {
  $("#field-owner").autocomplete("subjects", {
    formatItem: formatItem
  });
});