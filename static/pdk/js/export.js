//Load common code that includes config, then load the app logic for this page.
requirejs(['./common'], function (common) {
    requirejs(["bootstrap", "bootstrap-datepicker", "moment", "jquery"], function (bootstrap, bs_datepicker, moment, jquery)
    {
    	window.$ = jquery;
    	window.moment = moment;
    	
		$.ajaxSetup({ 
			beforeSend: function(xhr, settings) 
			{
				if (!(/^http:.*/.test(settings.url) || /^https:.*/.test(settings.url))) 
				{
					// Only send the token to relative URLs i.e. locally.
					xhr.setRequestHeader("X-CSRFToken", $.cookie('csrftoken'));
				}
			}
		});

		$('[data-toggle="tooltip"]').tooltip();

		$('#sources_select_all').change(function() 
		{
			$(".source_checkbox").prop("checked", $(this).is(":checked"));
		});
		
		$('.group_select_members').change(function(eventObj)
		{
			 const id = $(this).attr('id')
			 
			$('.' + id).prop("checked", $(this).is(":checked"));
		});

		$('#generators_select_all').change(function() 
		{
			$(".generator_checkbox").prop("checked", $(this).is(":checked"));
		});
		
		$('#data_start').datepicker();
		$('#data_end').datepicker();
	}); 
});