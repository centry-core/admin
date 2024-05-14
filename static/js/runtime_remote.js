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


$("#btn-manual").click(function() {
  var data = $("#ipt-manual").val();
  var result = [];
  //
  var pylons_data = data.split(";");
  //
  for (var i_idx in pylons_data) {
    var items = pylons_data[i_idx].split(":");
    //
    var pylon_id = items[0].trim();
    var plugins = items[1].split(",");
    //
    for (var j_idx in plugins) {
      var plugin = plugins[j_idx].trim();
      //
      result.push({
        "pylon_id": pylon_id,
        "name": plugin,
        "state": true,
      });
    }
  }
  //
  axios.post(remote_api_url, {data: result})
    .then(function (response) {
      showNotify("SUCCESS", "Update and restart requested")
    })
    .catch(function (error) {
      showNotify("ERROR", "Error during update and restart request")
      console.log(error);
    });
});
