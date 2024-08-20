$("#btn-execute").click(function() {
  $("#textarea-logs").val("");
  //
  axios.post(migration_db_api_url, {
      sqls: $("#textarea-sqls").val(),
      exceptions: $("#textarea-exceptions").val(),
    })
    .then(function (response) {
      showNotify("SUCCESS", "Action performed")
      $("#textarea-logs").val(response.data.logs);
    })
    .catch(function (error) {
      showNotify("ERROR", "Error during action")
      console.log(error);
    });
});
