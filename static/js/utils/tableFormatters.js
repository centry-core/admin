var roleTableFormatters = {
    checkboxFormatter: (value, row, index, field, edit_mode) => {
        const checked = value ? 'checked' : '';
        const disabled = edit_mode ? '' : 'disabled';
        return `
            <label
                class="mb-0 w-100 d-flex align-items-center custom-checkbox">
                <input
                    onchange="roleTableFormatters.updateCellCbx(this, '${index}', '${field}')" 
                    ${disabled}
                    ${checked}
                    type="checkbox">
            </label>
        `
    },
    updateCellCbx: (el, index, field) => {
        $(el.closest('table')).bootstrapTable(
            'updateCell',
            { index: +index, field: field, value: el.checked }
        )
    },
}