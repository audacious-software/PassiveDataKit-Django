//Load common code that includes config, then load the app logic for this page.
requirejs(['./common'], function (common) {
    requirejs(["bootstrap", "bootstrap-typeahead", "bootstrap-table"], function (bootstrap, bs_typeahead, bs_table)
    {
		$.ajaxSetup({ 
			beforeSend: function(xhr, settings) {
				if (!(/^http:.*/.test(settings.url) || /^https:.*/.test(settings.url))) {
					xhr.setRequestHeader("X-CSRFToken", $.cookie('csrftoken'));
				}
			}
		});

		$.get("unmatched-sources.json", function(data) {
	        $(".typeahead").typeahead({ source: data });
        });

		$('[data-toggle="tooltip"]').tooltip();
		
		$("select#field_assigned_group").change(function() {
			var groupId = $("select#field_assigned_group").val();
			
			if (groupId == "0") {
				$("#form-pdk-group-name").show();
			} else {
				$("#form-pdk-group-name").hide();
			}
		});
		
		var setupTableActions = function() {		
			$("a.remove_data_source").off("click");
			$("a.remove_data_source").click(function(eventObj) {
				eventObj.preventDefault();
			
				var name = $(this).attr("data-source-name");
				var pk = $(this).attr("data-source-pk");
			
				$("#remove_source_name").html(name);
			
				$("#delete_source_modal").modal("show");
			
				$("#btn_delete_source").off("click");

				$("button#btn_delete_source").click(function(eventObj) {
					$("#delete_source_pk").val(pk);

					$("#form_delete_source").submit();
				});
						
				return false;
			});

			$("a.move_data_source").off("click");
			$("a.move_data_source").click(function(eventObj) {
				eventObj.preventDefault();
			
				var name = $(this).attr("data-source-name");
				var pk = $(this).attr("data-source-pk");
			
				$("#move_source_name").html(name);
			
				$("#field_rename_existing").off("change");
				$("#field_move_existing").change(function() {
					if ($("#field_move_existing option:selected").val() == 0) {
						$("#move_new_group_fields").show();
					} else {
						$("#move_new_group_fields").hide();
					}
				});
			
				$("#move_new_group_fields").trigger("change");
			
				$("#move_source_modal").modal("show");
			
				$("#btn_move_source").off("click");
				$("button#btn_move_source").click(function(eventObj) {
					var groupPk = $("#field_move_existing option:selected").val();
					var groupName = $("#field_new_group_name_move").val()

					$("#move_source_pk").val(pk);
					$("#move_source_group_pk").val(groupPk);
					$("#move_source_group_name").val(groupName);
					
					if (groupPk == "0" && groupName.trim() == "") {
						alert("Please enter a new group name to continue.");
					} else {
						$("#field_new_group_name_move").val("");
						$("#form_move_source").submit();
					}
				});
						
				return false;
			});

			$("a.rename_data_source").off("click");
			$("a.rename_data_source").click(function(eventObj) {
				eventObj.preventDefault();
			
				var name = $(this).attr("data-source-name");
				var pk = $(this).attr("data-source-pk");
			
				$("#field_rename_existing").val(name);
			
				$("#rename_source_modal").modal("show");
			
				$("#btn_rename_source").off("click");
				$("#btn_rename_source").click(function(eventObj) {
					var name = $("#field_rename_existing").val()

					$("#rename_source_pk").val(pk);
					$("#rename_source_name").val(name);
					
					if (name.trim() == "") {
						alert("Please enter a new name to continue.");
					} else {
						$("#field_rename_existing").val("");
						$("#form_rename_source").submit();
					}
				});
						
				return false;
			});
		};

		$('table.group_table').on('sort.bs.table', function (e, name, order) {
			window.setTimeout(setupTableActions, 250);
		});

		$('table.group_table').on('page-change.bs.table', function (e, number, size) {
			window.setTimeout(setupTableActions, 250);
		});
		
		setupTableActions();
	}); 
});