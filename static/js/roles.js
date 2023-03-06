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
            roles_to_permissions: [],
            table_data: {},
            table_options: {},
            edit_mode: false,
        }
    },
    methods: {
        async get_permissions() {
            const response = await fetch('/api/v1/admin/permissions/')
            if (response.ok) {
                this.table_data = await response.json()
                this.roles_to_permissions = Array.from(new Set(this.roles.flatMap(role => role.name)));
            }
        },
        async get_roles() {
            const response = await fetch(`/api/v1/admin/roles`)
            if (response.ok) {
                this.roles = await response.json()
            }
        },
        async update_permissions() {
            const table_data = vueVm.registered_components.roles_table.table_action('getData')
            const response = await fetch('/api/v1/admin/permissions/', {
                method: 'PUT',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify(table_data)
            })
            if (response.ok) {
                console.log("Permissions updated")
                this.edit_mode = false
            }
        },
        changeMode() {
            this.edit_mode = !this.edit_mode;
            this.table_options.editable = this.edit_mode
        }
    },
    watch: {
        async edit_mode(new_value) {
            if (new_value === false) {
                await this.get_permissions()
            }
        },
        roles_to_permissions(new_roles) {
            const columns = [{
                field: 'name',
                title: 'Permission',
                sortable: true,
                searchable: true,
                editable: false,
            }]
            for (const role of new_roles) {
                columns.push({
                    field: role,
                    title: role,
                    formatter: (value, row, index, field) => roleTableFormatters.checkboxFormatter(value, row, index, field, this.edit_mode),
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
        await this.get_permissions();
        $('#searchRole').on('input', function ({target: {value}}) {
            $('#roles-table').bootstrapTable('filterBy', {
                name: value.toLowerCase()
            }, {
                'filterAlgorithm': (row, filters) => {
                    const name = filters ? filters.name : '';
                    return row.name.includes(name);
                }
            })
        })
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
                    <div class="d-flex justify-content-end">
                        <div class="custom-input custom-input_search custom-input_search__sm position-relative mr-2">
                            <input type="text" placeholder="Search" id="searchRole">
                            <img src="/design-system/static/assets/ico/search.svg" class="icon-search position-absolute">
                        </div>
                        <button v-if="!edit_mode" type="button" class="btn btn-secondary btn-icon btn-icon__purple mr-2" 
                            @click="changeMode">
                            <i class="icon__18x18 icon-edit"></i>
                        </button>
                        <div v-if="edit_mode">
                            <button type="button" @click="changeMode" 
                                id="project_submit" class="btn btn-secondary btn-basic">Cancel</button>
                            <button type="button" @click="update_permissions" 
                                id="project_submit" class="btn btn-basic ml-2">Save</button>
                        </div>
                    </div>
                </template>
            </TableCard>
        </div>
    </div>
   `
}
register_component('roles-page', RolesPage)
