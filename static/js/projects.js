function getPluginsList(){
  let selectedItems = vueVm.multiselectFilter.selectedItems
  let pluginsList = []
  selectedItems.forEach(item => pluginsList.push(item['id']))
  return pluginsList
}


function projectCreateSubmit() {
  fetch('/api/v1/projects/project/', {
      method: 'POST',
      headers: {'Content-Type': 'application/json'},
      body: JSON.stringify({
        "name": $('#project_name').val(),
        "owner": "",
        "vuh_limit": 60000,
        "plugins": getPluginsList(),
        "storage_space_limit": 1000000000,
        "data_retention_limit": 1000000000,
        "invitations": []
      })
  }).then(async response => {
      $("#projectCreateModal").modal('hide');
      data = await response.json()
      const newSections = data['plugins']
      const currentSection = "admin"
      const notAdmin = !vueVm.navbar.isAdmin

      if (notAdmin && !newSections.includes(currentSection) && newSections.length>0)
      {
        section = newSections[0]
        location.href = `/-/${section}`
        $('select.selectpicker[name=`section_select`]').val(section)
      } else {
          location.reload()
      }
  })
}



function projectActionFormatter(value, row, index) {
  return '<a href="/-/admin/projects/edit?project=' + row.id + '"><i class="fas fa-sync"></i></a>'
}

$(document).on('vue_init', () => {
    $('#project_submit').on('click', projectCreateSubmit)
})
