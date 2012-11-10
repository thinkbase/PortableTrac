jQuery(document).ready(function($) {
  $('#date_empty_option').hide();
  $('#type').change(function() {
    if ($('#type').val() == 'date') {
      $('#date_empty_option').show();
    } else {
      $('#date_empty_option').hide();
    }
  });
})
