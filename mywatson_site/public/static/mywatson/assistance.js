/* ************** Assistance panel ************** */

$('.assistance-btn').click(function() {
	panel = $('.assistance-panel')
	if ($(panel).is(':visible')) {
		$(panel).hide(250)
		// $('.assistance-btn').css('background', '#007EA7');

	} else {
		$(panel).show(250)
		// $('.assistance-btn').css('background', '#00A8E8');
	}
});
