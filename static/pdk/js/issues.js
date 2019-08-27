//Load common code that includes config, then load the app logic for this page.
requirejs(['./common'], function (common) {
    requirejs(["bootstrap", "bootstrap-typeahead", "bootstrap-table"], function (bootstrap, bs_typeahead, bs_table) {
		$.ajaxSetup({ 
			beforeSend: function(xhr, settings) {
				if (!(/^http:.*/.test(settings.url) || /^https:.*/.test(settings.url))) {
					xhr.setRequestHeader("X-CSRFToken", $.cookie('csrftoken'));
				}
			}
		});

		$("#issues-table").bootstrapTable({
			detailView: true,
			detailFormatter: function(index, row) {
				return "<strong>Description</strong><br />" + row["description"] + "<br /><br />" + row["user_agent"];
			},
			pagination: true,
			columns: [{
				title: 'Data Source',
				field: 'source',
				sortable: true
			}, {
				title: 'Model',
				field: 'model',
				sortable: true
			}, {
				title: 'Platform',
				field: 'platform',
				sortable: true
			}, {
				title: 'State',
				field: 'state',
				sortable: true
			}, {
				title: 'Created',
				field: 'created',
				sortable: true
			}, {
				title: 'Updated',
				field: 'updated',
				sortable: true
			}, {
				title: 'Issues',
				field: 'issues',
				formatter: function(value, row) {
					var issues = [];
					
					if (row["location_related"]) {
						issues.push("Location")
					}

					if (row["battery_use_related"]) {
						issues.push("Battery Usage")
					}
					
					if (row["storage_related"]) {
						issues.push("Storage")
					}
					
					if (row["power_management_related"]) {
						issues.push("Power Management")
					}
					
					if (row["data_quality_related"]) {
						issues.push("Data Quality")
					}
					
					if (row["data_volume_related"]) {
						issues.push("Data Volume")
					}
					
					if (row["bandwidth_related"]) {
						issues.push("Bandwidth")
					}
					
					if (row["uptime_related"]) {
						issues.push("App Uptime")
					}

					if (row["stability_related"]) {
						issues.push("App Stability")
					}
					
					if (row["configuration_related"]) {
						issues.push("App Configuration")
					}
					
					if (row["responsiveness_related"]) {
						issues.push("App Responsiveness")
					}
					
					if (issues.length == 0) {
						return "None Specified";
					}
					
					return issues.join(", ");
				},
				sortable: true
			}]
		});
		
		$("#add_issue_button").click(function(eventObj) {
			eventObj.preventDefault();
			
			var data = {};
			
			data["source"] = $("#source").val();
			data["description"] = $("#issue_description").val();

			data["location"] = $("#issue_location").is(":checked");
			data["battery"] = $("#issue_battery").is(":checked");
			data["power"] = $("#issue_power").is(":checked");
			data["data_quality"] = $("#issue_data_quality").is(":checked");
			data["data_volume"] = $("#issue_data_volume").is(":checked");
			data["bandwidth"] = $("#issue_bandwidth").is(":checked");
			data["storage"] = $("#issue_storage").is(":checked");
			data["app_uptime"] = $("#issue_app_uptime").is(":checked");
			data["app_stability"] = $("#issue_app_stability").is(":checked");
			data["app_configuration"] = $("#issue_app_configuration").is(":checked");
			data["app_responsiveness"] = $("#issue_app_responsiveness").is(":checked");
			
			$.post($("#issues-table").attr("data-url"), data, function(data) {
				alert(data["message"]);

				if (data["success"]) {
					$("#source").val("");
					$("#issue_description").val("");

					$("#issue_location").prop("checked", false);
					$("#issue_battery").prop("checked", false);
					$("#issue_power").prop("checked", false);
					$("#issue_data_quality").prop("checked", false);
					$("#issue_data_volume").prop("checked", false);
					$("#issue_bandwidth").prop("checked", false);
					$("#issue_storage").prop("checked", false);
					$("#issue_app_uptime").prop("checked", false);
					$("#issue_app_stability").prop("checked", false);
					$("#issue_app_configuration").prop("checked", false);
					$("#issue_app_responsiveness").prop("checked", false);

					$("#issues-table").bootstrapTable('refresh');
				}
			});
		});

		$.get("unmatched-sources.json", function(data) {
	        $(".typeahead").typeahead({ source: data });
        });

		if (window.setupHome != undefined) {
			window.setupHome();
		}
	}); 
});
