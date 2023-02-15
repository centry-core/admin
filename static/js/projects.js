function projectCreateSubmit() {
    fetch('/api/v1/projects/project/', {
        method: 'POST',
        headers: {'Content-Type': 'application/json'},
        body: JSON.stringify({
            "name": $('#project_name').val(),
            "owner": "",
            "vuh_limit": 60000,
            "plugins": vueVm.multiselectFilter?.selectedItems.map(i => i.id) || [],
            "storage_space_limit": 1000000000,
            "data_retention_limit": 1000000000,
            "invitations": []
        })
    }).then(async response => {
        $("#projectCreateModal").modal('hide');
        const data = await response.json()
        const newSections = data['plugins']
        const currentSection = "admin"
        const notAdmin = !vueVm.navbar.isAdmin

        if (notAdmin && !newSections.includes(currentSection) && newSections.length > 0) {
            const section = newSections[0]
            location.href = `/-/${section}`
            $('select.selectpicker[name=`section_select`]').val(section)
        } else {
            location.reload()
        }
    })
}


function projectActionFormatter(value, row, index) {
    return '<a href="/~/administration/~/projects/list/edit?project=' + row.id + '"><i class="fas fa-sync"></i></a>'
}

$(document).on('vue_init', () => {
    $('#project_submit').on('click', projectCreateSubmit)
})
