const fetchUsersAPI = async () => {
    const api_url = V.build_api_url('admin', 'users');
    const res = await fetch (`${api_url}/${getSelectedProjectId()}`,{
        method: 'GET',
    });
    return res.json();
}
const updateUserAPI = async (id, roles) => {
    const api_url = V.build_api_url('admin', 'users');
    const res = await fetch (`${api_url}/${getSelectedProjectId()}`,{
        method: 'PUT',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ id, roles })
    });
    return res;
}

const deleteUserAPI = async (id, roles) => {
    const api_url = V.build_api_url('admin', 'users');
    const res = await fetch (`${api_url}/${getSelectedProjectId()}`,{
        method: 'DELETE',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ id })
    });
    return res;
}

