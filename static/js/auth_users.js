$("#btn-delete-users").click(function() {
  axios.post(auth_users_api_url, {
      users: $("#table").bootstrapTable("getSelections"),
      action: "delete",
    })
    .then(function (response) {
      showNotify("SUCCESS", "Action performed")
    })
    .catch(function (error) {
      showNotify("ERROR", "Error during action")
      console.log(error);
    });
});
