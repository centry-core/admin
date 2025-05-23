// Database restore modal functionality
function refreshBackupList() {
  // Start list_backups task to get available backups
  axios.get(tasks_api_url, {params: {action: "start", scope: "list_backups:"}})
    .then(function (response) {
      if (response.data.ok) {
        console.log("Backup list refresh requested, waiting for results...");
        // Poll for task completion
        setTimeout(checkBackupListResults, 1000);
      } else {
        showNotify("ERROR", "Error listing backups: " + response.data.error);
      }
    })
    .catch(function (error) {
      showNotify("ERROR", "Error during backup list request");
      console.log(error);
    });
}

function checkBackupListResults() {
  // Get task status and results
  axios.get(tasks_api_url, {params: {action: "list", scope: "task"}})
    .then(function (response) {
      if (response.data && response.data.rows) {
        // Find the list_backups task
        var backupTask = response.data.rows.find(function(task) {
          return task.meta && task.meta.includes("list_backups") && task.status === "finished";
        });
        
        if (backupTask) {
          // Get the task result
          axios.get(tasks_api_url, {params: {action: "result", scope: backupTask.task_id}})
            .then(function (resultResponse) {
              if (resultResponse.data && resultResponse.data.status === "success") {
                // Update backup selector dropdown
                updateBackupSelector(resultResponse.data.backups);
              } else {
                $("#backup-selector").html('<option value="">No backups found</option>');
              }
            })
            .catch(function (error) {
              console.log("Error getting backup list results:", error);
            });
        } else {
          // Task still running or not found, check again in a second
          setTimeout(checkBackupListResults, 1000);
        }
      }
    })
    .catch(function (error) {
      console.log("Error checking backup list results:", error);
    });
}

function updateBackupSelector(backups) {
  if (!backups || backups.length === 0) {
    $("#backup-selector").html('<option value="">No backups found</option>');
    return;
  }
  
  var options = '<option value="">Select a backup</option>';
  backups.forEach(function(backup) {
    options += '<option value="' + backup.timestamp + '" data-schemas="' + backup.schemas.join(',') + '" data-date="' + backup.date + '">' 
      + backup.date + ' (' + backup.schemas.length + ' schemas)</option>';
  });
  
  $("#backup-selector").html(options);
}

// When a backup is selected, update the schema options
$("#backup-selector").change(function() {
  var selected = $(this).find("option:selected");
  var schemas = selected.data("schemas");
  var date = selected.data("date");
  
  if (schemas) {
    $("#backup-date").text(date);
    $("#backup-schemas").text(schemas);
    $("#backup-details").show();
    
    // Update project selector
    var schemaOptions = '<option value="">Select project</option>';
    schemas.split(',').forEach(function(schema) {
      if (schema !== 'shared') {
        schemaOptions += '<option value="' + schema + '">' + schema + '</option>';
      }
    });
    $("#project-selector").html(schemaOptions);
  } else {
    $("#backup-details").hide();
  }
});

// Show/hide project selector based on schema selection
$("#schema-selector").change(function() {
  if ($(this).val() === "project") {
    $("#project-selector-container").show();
  } else {
    $("#project-selector-container").hide();
  }
});

// Handle restore button click
$("#btn-confirm-restore").click(function() {
  var timestamp = $("#backup-selector").val();
  var schemaType = $("#schema-selector").val();
  var projectId = $("#project-selector").val();
  
  if (!timestamp) {
    showNotify("ERROR", "Please select a backup to restore");
    return;
  }
  
  var param = timestamp;
  
  // Construct the parameter based on selections
  if (schemaType === "shared") {
    param += ":shared";
  } else if (schemaType === "project" && projectId) {
    param += ":" + projectId;
  } else if (schemaType === "all") {
    param += ":all";
  } else if (schemaType === "project" && !projectId) {
    showNotify("ERROR", "Please select a project to restore");
    return;
  }
  
  // Confirm before proceeding
  if (confirm("WARNING: This will overwrite existing data. Are you sure you want to restore from the selected backup?")) {
    $("#task-selector").val("restore_database");
    $("#task-param").val(param);
    $("#btn-start-task").click();
    $("#modal-restore-db").modal('hide');
  }
});

// Initialize backup list when modal opens
$("#modal-restore-db").on("show.bs.modal", function() {
  refreshBackupList();
});
