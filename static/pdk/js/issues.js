//Load common code that includes config, then load the app logic for this page.
requirejs(['./common'], function (common) {
    requirejs(["bootstrap", "bootstrap-typeahead", "bootstrap-table", "moment"], function (bootstrap, bs_typeahead, bs_table, moment) {
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
				sortable: true,
				formatter: function(value, row) {
					return '<a href="source/' + value + '" target="_blank">' + value + '</a>';
				}
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
				sortable: true,
				formatter: function(value, row) {
					const date = moment(value);
					
					return date.format('lll');
				}
			}, {
				title: 'Updated',
				field: 'updated',
				sortable: true,
				formatter: function(value, row) {
					const date = moment(value);
					
					return date.format('lll');
				}
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

					if (row["correctness_related"]) {
						issues.push("App Correctness")
					}

					if (row["ui_related"]) {
						issues.push("App User Interface / Interactions")
					}

					if (row["device_peformance_related"]) {
						issues.push("Device Performance")
					}

					if (row["device_stability_related"]) {
						issues.push("Device Stability")
					}
					
					if (issues.length == 0) {
						return "None Specified";
					}
					
					return issues.join(", ");
				},
				sortable: true
			}]
		});
		
		$.get($("#issues-table").attr("data-issues-url"), function(data) {
		    $("#issues-table").bootstrapTable("load", data)
		});
		
		var cachedData = null;
		
		var applyFilter = function() {
			console.log("FILTERING!");
			
			var toShow = new Set();
		    
		    if (cachedData == null) {
			    cachedData = JSON.parse(JSON.stringify($("#issues-table").bootstrapTable("getData")));
		    }

		    var tableData = JSON.parse(JSON.stringify(cachedData));

		    console.log(tableData);
		    
			$(".issue_state_filter").each(function(index) {
				if ($(this).is(":checked")) {
					var state = $(this).attr("data-value");
					
					for (var i = 0; i < tableData.length; i++) {
						var item = tableData[i];
						
						if (item["state"] == state) {
							toShow.add(i);
						}
					}
				}
			});

			var typeMatches = new Set();

			$(".issue_type_filter").each(function(index) {
				if ($(this).is(":checked")) {
					var issue_type = $(this).attr("data-key");
					
					for (var i = 0; i < tableData.length; i++) {
						var item = tableData[i];

						if (issue_type == "any_issue") {
							typeMatches.add(i);
						} else if (item[issue_type] != undefined && item[issue_type] == true) {
							typeMatches.add(i);
						}
					}
				}
			});

			var mfgrMatches = new Set();

			$(".issue_mfgr_filter").each(function(index) {
				if ($(this).is(":checked")) {
					var manufacturer = $(this).attr("data-value");
					
					for (var i = 0; i < tableData.length; i++) {
						var item = tableData[i];
						
						if (manufacturer == "any") {
							mfgrMatches.add(i);
						} else  if (item['model'].endsWith("(" + manufacturer + ")")) {
							mfgrMatches.add(i);
						}
					}
				}
			});

			var searchMatches = new Set();
			
			var searchQuery = $("#issue_search").val();
			
			if (searchQuery == undefined) {
				searchQuery = "";
			}
			
			for (var i = 0; i < tableData.length; i++) {
				if (searchQuery == "") {
					searchMatches.add(i);
				} else {
					var item = tableData[i];
				
					if (item["description"] != null && item["description"].toLowerCase().indexOf(searchQuery.toLowerCase()) != -1) {
						searchMatches.add(i);
					}

					if (item["platform"] != null && item["platform"].toLowerCase().indexOf(searchQuery.toLowerCase()) != -1) {
						searchMatches.add(i);
					}

					if (item["user_agent"] != null && item["user_agent"].toLowerCase().indexOf(searchQuery.toLowerCase()) != -1) {
						searchMatches.add(i);
					}

					if (item["model"] != null && item["model"].toLowerCase().indexOf(searchQuery.toLowerCase()) != -1) {
						searchMatches.add(i);
					}
				}
			}
			
			var toDelete = new Set();
			
			for (var visible of toShow) {
				if (typeMatches.has(visible)) {
					// Do nothing...
				} else {
					toDelete.add(visible);
				}
			}

			for (var visible of toShow) {
				if (mfgrMatches.has(visible)) {
					// Do nothing...
				} else {
					toDelete.add(visible);
				}
			}

			for (var visible of toShow) {
				if (searchMatches.has(visible)) {
					// Do nothing...
				} else {
					toDelete.add(visible);
				}
			}

			for (var remove of toDelete) {
				toShow.delete(remove);
			}

			for (var i = tableData.length - 1; i >= 0; i--) {
				if (toShow.has(i)) {
					// Keep
				} else {
					tableData.splice(i, 1);
				}
			}

		    $("#issues-table").bootstrapTable("load", tableData);
		}
		
		$(".issue_state_filter").click(function() {
			applyFilter();
		});

		$(".issue_type_filter").click(function() {
			applyFilter();
		});

		$(".issue_mfgr_filter").click(function() {
			applyFilter();
		});

		$("#issue_search").on('input', function() {
			applyFilter();
		});
		
		$("#add_issue_button").click(function(eventObj) {
			eventObj.preventDefault();
			
			var data = {};
			
			data["source"] = $("#source").val();
			data["description"] = $("#issue_description").val();
			data["tags"] = $("#issue_tags").val();

			data["app_stability"] = $("#issue_app_stability").is(":checked");
			data["app_uptime"] = $("#issue_app_uptime").is(":checked");
			data["app_responsiveness"] = $("#issue_app_responsiveness").is(":checked");
			data["battery"] = $("#issue_battery").is(":checked");
			data["power"] = $("#issue_power").is(":checked");
			data["data_volume"] = $("#issue_data_volume").is(":checked");
			data["data_quality"] = $("#issue_data_quality").is(":checked");
			data["bandwidth"] = $("#issue_bandwidth").is(":checked");
			data["storage"] = $("#issue_storage").is(":checked");
			data["app_configuration"] = $("#issue_app_configuration").is(":checked");
			data["location"] = $("#issue_location").is(":checked");
			data["app_correctness"] = $("#issue_app_correctness").is(":checked");
			data["app_ui"] = $("#issue_app_ui").is(":checked");
			data["device_performance"] = $("#issue_device_performance").is(":checked");
			data["device_stability"] = $("#issue_device_stability").is(":checked");
			
			$.post($("#issues-table").attr("data-issues-url"), data, function(data) {
				alert(data["message"]);

				if (data["success"]) {
					$("#source").val("");
					$("#issue_description").val("");
					$("#issue_tags").val("");

					$(".pdk-issue-type").prop("checked", false);

					$.get($("#issues-table").attr("data-issues-url"), function(data) {
						$("#issues-table").bootstrapTable("load", data)
						
						cachedData = null;
					
						applyFilter();
					});
				}
			});
		});

		if (window.setupHome != undefined) {
			window.setupHome();
		}
	}); 
});
