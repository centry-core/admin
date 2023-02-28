function checkboxFormatter(value, row, index, edit_mode) {
    const checked = value ? 'checked' : '';
    const disabled = edit_mode ? '' : 'disabled';
    return `<input type="checkbox" ${checked} ${disabled}>`;
}

const RolesPage = {
    delimiters: ['[[', ']]'],
    data() {
        return {
            table_attributes: {
                'data-pagination': 'true',
                'data-side-pagination': 'client',
                'id': 'roles-table',
                "data-search-selector": "#customSearch"
            },
            roles: [],
            table_data: {},
            table_options: {},
            edit_mode: true,
        }
    },
    methods: {
        async get_roles() {
            const response = await fetch('/api/v1/admin/permissions/')
            if (response.ok) {
                this.table_data = await response.json()
                const roles = this.table_data.rows.map(row => row.roles).flat();
                this.roles = Array.from(new Set(roles.flatMap(role => Object.keys(role))));
            }
        },
        changeMode() {
            this.edit_mode = !this.edit_mode;
            this.table_options.editable = this.edit_mode
        }
    },
    watch: {
        roles(new_roles) {
            const columns = [{
                field: 'name',
                title: 'Permission',
                sortable: true,
                searchable: true,
                editable: false,
            }]
            for (const role of new_roles) {
                columns.push({
                    field: "roles." + role,
                    title: role,
                    formatter: (value, row, index) => checkboxFormatter(value, row, index, this.edit_mode),
                    sortable: false
                })
            }
            this.table_options = {
                data: this.table_data,
                columns: columns,
                search: true,
            }
        },
        table_options: {
            handler(newValue, oldValue) {
                vueVm.registered_components.roles_table.table_action('refreshOptions', newValue)
            },
            deep: true,
        },
    },
    async mounted() {
        await this.get_roles()
    },
    template: `
<div class="d-flex">
  <div class="card-body">
      <TableCard
        ref="roles_table"
        header='Roles'
        @register="$root.register"
        instance_name="roles_table"
        :table_attributes="table_attributes"
        :events="events"
        >
        <template #actions="{master}">
            <div class="form-group text-right mb-0 row">
            <div class="custom-input custom-input__sm custom-input_search position-relative mr-2 w-50">
            <input
                id="customSearch"
                type="text"
                placeholder="Search">
            <img src="/design-system/static/assets/ico/search.svg" class="icon-search position-absolute">
            </div class="col">
                <button type="button" class="btn btn-secondary btn-icon btn-icon__purple mr-2" 
                    @click="changeMode">
                <i class="fas fa-edit"></i>
            </button>
            </div>
        </template>
    </TableCard>
  </div>
</div>
   `
}
register_component('roles-page', RolesPage)
