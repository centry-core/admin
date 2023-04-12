const UsersPage = {
    props: ['instance_name'],
    components: {
        'users-modal-confirm': UsersModalConfirm,
    },
    data() {
        return {
            table_attributes: {
                'data-pagination': 'true',
                'data-side-pagination': 'client',
                'data-unique-id': "id",
                'id': 'usersTable',
                'data-page-list': '[5, 10, 15, 20]',
                'data-page-size': 5,
                'data-pagination-parts': ['pageInfo', 'pageList', 'pageSize'],
            },
            loadingApply: false,
            isValidFilter: false,
            applyClicked: false,
            newUser: {
                email: '',
                roles: [],
            },
            selectedRoles: [],
            tableColumns: null,
            tableData: null,
            allExistedRoles: ['admin', 'viewer', 'editor', 'hacker'],
            selectedRows: [],
            showConfirmModal: false,
            loadingDelete: false,
            needRedraw: false,
        }
    },
    watch: {
        newUser: {
            handler: function (newVal, oldVal) {
                if (newVal.email && oldVal.email) {
                    const arr = [];
                    $('#newUserBlock > div').each(function (index, element) {
                        $(element).find('div.cell-input > div').each(function (index, cell) {
                            arr.push(cell.getAttribute('data-valid'));
                        })
                    })
                    this.isValidFilter = arr.every(elem => elem === 'true')
                }
            },
            deep: true
        }
    },
    computed: {
        canRemove() {
            return this.selectedRows.length > 0;
        }
    },
    mounted() {
        $(document).on('vue_init', () => {
            this.fetchUsers();
        })
    },
    methods: {
        fetchUsers() {
            fetchUsersAPI().then(res => {
                this.tableData = res.rows;
                this.generateTableOptions();
                $(".dropdown-menu.close-outside").on("click", function (event) {
                    event.stopPropagation();
                });
                $('#usersTable').on('check.bs.table', (row, $element) => {
                    this.getSelection();
                });
                $('#usersTable').on('uncheck.bs.table', (row, $element) => {
                    this.getSelection();
                });
                $('#usersTable').on('uncheck-all.bs.table', (row, $element) => {
                    this.getSelection();
                });
                $('#usersTable').on('check-all.bs.table', (rowsAfter, rowsBefore) => {
                    this.getSelection();
                });
            })
        },
        getSelection() {
            this.selectedRows = $('#usersTable').bootstrapTable('getSelections');
        },
        generateColumns() {
            return [
                {
                    checkbox: true,
                },
                {
                    field: 'name',
                    title: 'name',
                    sortable: true,
                    class: 'min-w-175',
                },
                {
                    field: 'email',
                    title: 'email',
                    sortable: true,
                    class: 'min-w-175',
                },
                {
                    field: 'role',
                    title: 'role',
                    class: 'max-w-175',
                    formatter: (value, row, index, field) => userTableFormatters.selectRoleFormatter(value, row, index, field, this.allExistedRoles),
                },
                {
                    class: 'w-12',
                    formatter: (value, row, index, field) => userTableFormatters.action(value, row, index, field),
                    events: userTableFormatters.action_events,
                },
            ]
        },
        generateTableOptions() {
            $('#usersTable').bootstrapTable('destroy').bootstrapTable({
                data: this.tableData,
                columns: this.generateColumns(),
                undefinedText: '',
            })
        },
        async inviteUser({ email, roles }) {
            const api_url = this.$root.build_api_url('admin', 'users');
            const res = await fetch (`${api_url}/${getSelectedProjectId()}`,{
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({
                    "name": email,
                    "email": email,
                    "roles": roles
                })
            });
            return res.json();
        },
        hasError(value) {
            return value.length > 0;
        },
        showError(value) {
            return this.applyClicked ? value.length > 0 : true;
        },
        apply() {
            this.applyClicked = true;
            if (this.isValidFilter) {
                this.inviteUser(this.newUser).then(res => {
                    showNotify('SUCCESS', 'User invited');
                    this.newUser.email = '';
                    this.newUser.roles = [];
                    this.fetchUsers();
                    this.applyClicked = false;
                    this.needRedraw = true;
                    this.isValidFilter = false;
                }).finally(() => {
                    this.needRedraw = false;
                })
            }
        },
        handleDeleteUser() {
            this.loadingDelete = true;
            const userIds = this.selectedRows.map(user => user.id);
            deleteUserAPI(userIds).then(res => {
                setTimeout(() => {
                    showNotify('SUCCESS', 'User deleted')
                    this.showConfirmModal = false;
                    this.loadingDelete = false;
                }, 500)
            })
        }
    },
    template: `
        <div class="m-3">
            <TableCard
                header='Users'
                ref="users_table"
                :table_attributes="table_attributes"
                :events="events"
                :adaptive-height="true"
                >
                <template #actions="{master}">
                    <div class="d-flex justify-content-end">
                        <div class="custom-input custom-input_search__sm position-relative mb-3 mr-2" style="">
                            <input id="bucketSearch" type="text" placeholder="Bucket name">
                            <img src="/design-system/static/assets/ico/search.svg" class="icon-search position-absolute">
                        </div>
                        <button id="removeButton" type="button" :disabled="!canRemove" class="btn btn-secondary btn-icon btn-icon__purple"
                            @click="showConfirmModal = true">
                            <i class="fas fa-trash-alt"></i>
                        </button>
                    </div>
                </template>
                <template #extra="{master}">
                    <div id="newUserBlock" class="d-flex">
                        <div class="mr-2 flex-grow-1 cell-input">
                            <p class="font-h6 font-semibold mb-1">Email Addresses</p>
                            <div class="custom-input custom-input__sm" :class="{'invalid-input': !showError(newUser.email)}"
                                :data-valid="hasError(newUser.email)">
                                <input
                                    type="text"
                                    v-model="newUser.email"
                                    placeholder="Enter email or emails separated by comma">
                                <span class="input_error-msg">Email is required!</span>
                            </div>
                        </div>
                        <div class="mr-2 cell-input" style="min-width: 250px">
                            <p class="font-h6 font-semibold mb-1">Roles</p>
                            <div class="select-validation" :class="{'invalid-select': !showError(newUser.roles)}"
                                :data-valid="hasError(newUser.roles)">
                                <multiselect-dropdown
                                    :key="needRedraw"
                                    @register="register"
                                    placeholder="Select role"
                                    v-model:modelValue="newUser.roles"
                                    button_class="btn-select__sm btn btn-select dropdown-toggle d-inline-flex align-items-center"
                                    :list_items="allExistedRoles"
                                    :has_error_class="{'invalid-select': !showError(newUser.roles)}"
                                    instance_name="multiselect_dropdown_1"
                                ></multiselect-dropdown>
                                <span class="select_error-msg">Role is required!</span>
                            </div>
                        </div>
                        <div class="pt-1">
                            <button class="btn btn-basic d-flex align-items-center mt-3"
                                type="button"
                                @click="apply">Invite
                                    <i v-if="loadingApply" class="preview-loader__white ml-2"></i>
                            </button>
                        </div>
                    </div>
                </template>
            </TableCard>
            <Transition>
                <users-modal-confirm
                    v-if="showConfirmModal"
                    :loadingDelete="loadingDelete"
                    @close-confirm="showConfirmModal = false"
                    @delete="handleDeleteUser">
                </users-modal-confirm>
            </Transition>
        </div>
   `
}
register_component('users-page', UsersPage);