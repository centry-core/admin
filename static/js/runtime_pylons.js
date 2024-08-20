$("#modal-pylon-logs").on("show.bs.modal", function (e) {
  $("#modal-logs-pylon").text(logs_row.pylon_id);
  $("#input-logs").val("");
});


$("#btn-load").click(function() {
  axios.post(logs_api_url, {pylon_id: logs_row.pylon_id})
    .then(function (response) {
      $("#input-logs").val(response.data.logs);
    })
    .catch(function (error) {
      showNotify("ERROR", "Error during logs retrieval")
      console.log(error);
    });
});


function pylonsActionsFormatter(value, row, index) {
  return [
    '<a class="task-show-logs" href="javascript:void(0)" title="Show logs">',
    '<i class="fa fa-file-text" style="color: #858796"></i>',
    '</a>',
  ].join('')
}


window.pylonsActionsEvents = {
  "click .task-show-logs": function (e, value, row, index) {
    logs_row = row;
    $("#modal-pylon-logs").modal("show");
  }
}