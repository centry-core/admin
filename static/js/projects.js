const set_errors = error_data => {
    error_data?.forEach(err => {
        err.loc?.forEach(i => {
            const inpt = $(`#${i}`)
            inpt.addClass('is-invalid')
            inpt.siblings('.invalid-feedback').text(err.msg)
        })
    })
}

const clear_errors = () => {
    ['name', 'project_admin_email'].forEach(i => {
        $(`#${i}`).removeClass('is-invalid')
    })
}

async function projectCreateSubmit() {
    clear_errors()
    const api_url = V.build_api_url('projects', 'project', {trailing_slash: true})
    const resp = await fetch(api_url, {
        method: 'POST',
        headers: {'Content-Type': 'application/json'},
        body: JSON.stringify({
            "name": $('#name').val(),
            "project_admin_email": $('#project_admin_email').val(),
            "vuh_limit": 60000,
            "plugins": vueVm.multiselectFilter?.selectedItems.map(i => i.id) || [],
            "storage_space_limit": 1000000000,
            "data_retention_limit": 1000000000,
        })
    })
    if (resp.ok) {
        $("#projectCreateModal").modal('hide');
        const data = await resp.json()
        const newSections = data['plugins']
        const currentSection = "admin"
        const notAdmin = !vueVm.navbar.isAdmin

        if (notAdmin && !newSections.includes(currentSection) && newSections.length > 0) {
            const section = newSections[0]
            location.href = `/-/${section}`
            $('select.selectpicker[name="section_select"]').val(section)
        } else {
            location.reload()
        }
    } else {
        const err_data = await resp.json()
        set_errors(err_data)
    }
}

function projectActionFormatter(value, row, index) {
    return '<a href="/~/administration/~/projects/list/edit?project=' + row.id + '"><i class="fas fa-sync"></i></a>'
}

$(document).on('vue_init', () => {
    $('#project_submit').on('click', projectCreateSubmit)
})
