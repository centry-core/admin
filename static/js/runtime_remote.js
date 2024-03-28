$("#btn-update").click(function() {
  var data = $("#table").bootstrapTable("getSelections");
  //
  axios.post(remote_api_url, {data: data})
    .then(function (response) {
      showNotify("SUCCESS", "Update and restart requested")
    })
    .catch(function (error) {
      showNotify("ERROR", "Error during update and restart request")
      console.log(error);
    });
});
