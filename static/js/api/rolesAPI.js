const fetchPermissionsAPI = (selectedMode) => {
    return fetch(`/api/v1/admin/permissions/${selectedMode}`).then((data) => {
        return data.json()
    })
}
const fetchRolesAPI = (selectedMode) => {
    return fetch(`/api/v1/admin/roles/${selectedMode}`).then((data) => {
        return data.json()
    })
}
const saveRolesPermissionsAPI = async (tableData, selectedMode) => {
    const res = await fetch(`/api/v1/admin/permissions/${selectedMode}`, {
        method: 'PUT',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify(tableData)
    })
    return res.json();
}
const createRoleAPI = async (newRoleName, selectedMode) => {
    const res = await fetch(`/api/v1/admin/roles/${selectedMode}`, {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify({name: newRoleName})
    })
    return res.json();
}
const deleteRoleAPI = async (roleName, selectedMode) => {
    const res = await fetch(`/api/v1/admin/roles/${selectedMode}`, {
        method: 'DELETE',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify({name: roleName})
    })
    return res.json();
}
const updateRoleNameAPI = async (oldRoleName, newRoleName, selectedMode) => {
    const res = await fetch(`/api/v1/admin/roles/${selectedMode}`, {
        method: 'PUT',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify({name: oldRoleName, new_name: newRoleName})
    })
    return res.json();
}