jQuery(document).ready(function($) {
  $("[id$=reassign_owner]").autocomplete("../subjects", {
    formatItem: formatItem
  });
});