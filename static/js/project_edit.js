function userAddSubmit() {
  fetch(window.url_prefix + '/api/v1/admin/users/' + project + '/', {
      method: 'POST',
      headers: {'Content-Type': 'application/json'},
      body: JSON.stringify({
        "name": $('#user_name').val(),
      })
  }).then(response => {
      $("#userAddModal").modal('hide');
      location.reload();
  })
}

$(document).on('vue_init', () => {
    $('#project_user_submit').on('click', userAddSubmit)
})
