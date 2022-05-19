function projectCreateSubmit() {
  fetch('/api/v1/projects/project/', {
      method: 'POST',
      headers: {'Content-Type': 'application/json'},
      body: JSON.stringify({
        "name": $('#project_name').val(),
        "owner": "",
        "vuh_limit": 60000,
        "plugins": ["backend","visual","code","application","cloud","infra","dashboards","portfolio","scheduler"],
        "storage_space_limit": 1000000000,
        "data_retention_limit": 1000000000,
        "invitations": []
      })
  }).then(response => {
      $("#projectCreateModal").modal('hide');
      location.reload();
  })
}

function projectActionFormatter(value, row, index) {
  return '<a href="/-/admin/projects/edit?project=' + row.id + '"><i class="fas fa-sync"></i></a>'
}

$(document).on('vue_init', () => {
    $('#project_submit').on('click', projectCreateSubmit)
})
