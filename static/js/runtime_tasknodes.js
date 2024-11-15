$(".refresh-table-button").click(function() {
  $($(this).data("target")).bootstrapTable("refresh", {});
});

$(".refresh-pool-button").click(function() {
  var target = $(this).data("target");
  //
  axios.get(tasknodes_api_url, {params: {action: "refresh", node: $(this).data("node"), scope: "pool"}})
    .then(function (response) {
      if (response.data.ok) {
        showNotify("SUCCESS", "Refresh request completed");
        $(target).bootstrapTable("refresh", {});
      } else {
        showNotify("ERROR", response.data.error);
      }
    })
    .catch(function (error) {
      showNotify("ERROR", "Error during refresh request");
      console.log(error);
    });
});

$(".refresh-task-button").click(function() {
  var target = $(this).data("target");
  //
  axios.get(tasknodes_api_url, {params: {action: "refresh", node: $(this).data("node"), scope: "task"}})
    .then(function (response) {
      if (response.data.ok) {
        showNotify("SUCCESS", "Refresh request completed");
        $(target).bootstrapTable("refresh", {});
      } else {
        showNotify("ERROR", response.data.error);
      }
    })
    .catch(function (error) {
      showNotify("ERROR", "Error during refresh request");
      console.log(error);
    });
});
