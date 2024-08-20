$("#btn-add-user-project-defaults").click(function() {
  $("#textarea-logs").val("");
  //
  axios.post(migration_permissions_api_url, {mode: "add_user_project_defaults"})
    .then(function (response) {
      showNotify("SUCCESS", "Action performed")
      $("#textarea-logs").val(response.data.logs);
    })
    .catch(function (error) {
      showNotify("ERROR", "Error during action")
      console.log(error);
    });
});
