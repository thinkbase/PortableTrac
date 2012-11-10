jQuery(document).ready(function($) {
    jQuery('.datepick').datepicker({
        firstDay: datefield['first_day'],
        dateFormat: datefield['format'],
        defaultDate: 0,
        showOn: "both",
        weekHeader: 'W',
        showWeek: datefield['show_week'],
        showButtonPanel: datefield['show_panel'],
        numberOfMonths: datefield['num_months'],
        changeMonth: datefield['change_month'],
        changeYear: datefield['change_year'],
        buttonImage: datefield['calendar'],
        buttonImageOnly: true
    });
});
