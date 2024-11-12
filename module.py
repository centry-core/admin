#!/usr/bin/python3
# coding=utf-8

#   Copyright 2022 getcarrier.io
#
#   Licensed under the Apache License, Version 2.0 (the "License");
#   you may not use this file except in compliance with the License.
#   You may obtain a copy of the License at
#
#       http://www.apache.org/licenses/LICENSE-2.0
#
#   Unless required by applicable law or agreed to in writing, software
#   distributed under the License is distributed on an "AS IS" BASIS,
#   WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
#   See the License for the specific language governing permissions and
#   limitations under the License.

""" Module """
from pylon.core.tools import log  # pylint: disable=E0401
from pylon.core.tools import module  # pylint: disable=E0401

from tools import theme, VaultClient  # pylint: disable=E0401
import hvac


class Module(module.ModuleModel):
    """ Pylon module """

    def __init__(self, context, descriptor):
        self.context = context
        self.descriptor = descriptor
        #
        # self.db = Holder()  # pylint: disable=C0103
        # self.db.tbl = Holder()
        #
        self.remote_runtimes = {}

    def init(self):
        """ Init module """
        log.info("Initializing module")
        # Run DB migrations
        # db_migrations.run_db_migrations(self, db.url)
        # DB
        # Theme registration
        #
        # System: for landing info screen
        #
        theme.register_section(
            "system", "System",
            kind="holder",
            hidden=True,
            location="left",
            permissions=[],
            # icon_class="fas fa-info-circle fa-fw",
        )
        theme.register_subsection(
            "system",
            "status", "Status",
            title="Status",
            kind="slot",
            hidden=True,
            permissions=[],
            prefix="admin_system_status_",
            # icon_class="fas fa-server fa-fw",
            # weight=2,
        )
        theme.register_page(
            "system", "status", "empty",
            title="Empty",
            kind="slot",
            permissions=[],
            prefix="admin_system_status_empty_",
        )
        #
        # Administration mode
        #
        theme.register_mode(
            "administration", "Administration",
        )
        theme.register_mode_section(
            "administration", "projects", "Projects",
            kind="holder",
            location="left",
            permissions={
                "permissions": ["projects"],
                "recommended_roles": {
                    "administration": {"admin": True, "viewer": False, "editor": False},
                    "default": {"admin": True, "viewer": False, "editor": False},
                    "developer": {"admin": True, "viewer": False, "editor": False},
                }},
            # icon_class="fas fa-info-circle fa-fw",
        )
        theme.register_mode_subsection(
            "administration", "projects",
            "list", "Projects",
            title="Projects",
            kind="slot",
            permissions={
                "permissions": ["projects.projects"],
                "recommended_roles": {
                    "administration": {"admin": True, "viewer": False, "editor": False},
                    "default": {"admin": True, "viewer": False, "editor": False},
                    "developer": {"admin": True, "viewer": False, "editor": False},
                }},
            prefix="admin_mode_projects_",
            # icon_class="fas fa-server fa-fw",
            # weight=2,
        )
        theme.register_mode_page(
            "administration", "projects",
            "list", "edit",
            title="Edit",
            kind="slot",
            permissions={
                "permissions": ["projects.projects"],
                "recommended_roles": {
                    "administration": {"admin": True, "viewer": False, "editor": False},
                    "default": {"admin": True, "viewer": False, "editor": False},
                    "developer": {"admin": True, "viewer": False, "editor": False},
                }},
            prefix="admin_mode_projects_edit_",
        )
        #
        theme.register_mode_section(
            "administration", "configuration", "Configuration",
            kind="holder",
            location="left",
            permissions={
                "permissions": ["configuration"],
                "recommended_roles": {
                    "administration": {"admin": True, "viewer": True, "editor": True},
                    "default": {"admin": True, "viewer": True, "editor": True},
                    "developer": {"admin": True, "viewer": True, "editor": True},
                }},
            # icon_class="fas fa-info-circle fa-fw",
        )
        #
        theme.register_mode_subsection(
            "administration", "configuration",
            "roles", "Roles",
            title="Roles",
            kind="slot",
            permissions={
                "permissions": ["configuration.roles"],
                "recommended_roles": {
                    "administration": {"admin": True, "viewer": False, "editor": False},
                    "default": {"admin": True, "viewer": False, "editor": False},
                    "developer": {"admin": True, "viewer": False, "editor": False},
                }},
            prefix="admin_mode_roles_",
            # icon_class="fas fa-server fa-fw",
            # weight=2,
        )
        theme.register_subsection(
            "configuration",
            "roles", "Roles",
            title="Roles",
            kind="slot",
            permissions={
                "permissions": ["configuration.roles"],
                "recommended_roles": {
                    "administration": {"admin": True, "viewer": False, "editor": False},
                    "default": {"admin": True, "viewer": False, "editor": False},
                    "developer": {"admin": True, "viewer": False, "editor": False},
                }},
            prefix="roles_",
        )
        theme.register_subsection(
            "configuration",
            "users", "Users",
            title="Users",
            kind="slot",
            permissions={
                "permissions": ["configuration.users"],
                "recommended_roles": {
                    "administration": {"admin": True, "viewer": False, "editor": False},
                    "default": {"admin": True, "viewer": False, "editor": False},
                    "developer": {"admin": True, "viewer": False, "editor": False},
                }},
            prefix="users_",
        )
        #
        # Modes
        #
        theme.register_mode_section(
            "administration", "modes", "Modes",
            kind="holder",
            permissions={
                "permissions": ["modes"],
                "recommended_roles": {
                    "administration": {"admin": True, "viewer": False, "editor": False},
                    "default": {"admin": True, "viewer": False, "editor": False},
                    "developer": {"admin": True, "viewer": False, "editor": False},
                }
            },
            location="left",
            icon_class="fas fa-info-circle fa-fw",
        )
        theme.register_mode_subsection(
            "administration", "modes",
            "users", "Users",
            title="Users",
            kind="slot",
            permissions={
                "permissions": ["modes.users"],
                "recommended_roles": {
                    "administration": {"admin": True, "viewer": False, "editor": False},
                    "default": {"admin": True, "viewer": False, "editor": False},
                    "developer": {"admin": True, "viewer": False, "editor": False},
                }
            },
            prefix="admin_modes_users_",
            icon_class="fas fa-server fa-fw",
        )
        #
        # Runtime
        #
        theme.register_mode_section(
            "administration", "runtime", "Runtime",
            kind="holder",
            permissions={
                "permissions": ["runtime"],
                "recommended_roles": {
                    "administration": {"admin": True, "viewer": False, "editor": False},
                    "default": {"admin": True, "viewer": False, "editor": False},
                    "developer": {"admin": True, "viewer": False, "editor": False},
                }
            },
            location="left",
            icon_class="fas fa-info-circle fa-fw",
        )
        theme.register_mode_subsection(
            "administration", "runtime",
            "plugins", "Plugins",
            title="Plugins",
            kind="slot",
            permissions={
                "permissions": ["runtime.plugins"],
                "recommended_roles": {
                    "administration": {"admin": True, "viewer": False, "editor": False},
                    "default": {"admin": True, "viewer": False, "editor": False},
                    "developer": {"admin": True, "viewer": False, "editor": False},
                }
            },
            prefix="admin_runtime_plugins_",
            icon_class="fas fa-server fa-fw",
        )
        theme.register_mode_subsection(
            "administration", "runtime",
            "remote", "Remote",
            title="Remote",
            kind="slot",
            permissions={
                "permissions": ["runtime.plugins"],
                "recommended_roles": {
                    "administration": {"admin": True, "viewer": False, "editor": False},
                    "default": {"admin": True, "viewer": False, "editor": False},
                    "developer": {"admin": True, "viewer": False, "editor": False},
                }
            },
            prefix="admin_runtime_remote_",
            icon_class="fas fa-server fa-fw",
        )
        theme.register_mode_subsection(
            "administration", "runtime",
            "pylons", "Pylons",
            title="Pylons",
            kind="slot",
            permissions={
                "permissions": ["runtime.plugins"],
                "recommended_roles": {
                    "administration": {"admin": True, "viewer": False, "editor": False},
                    "default": {"admin": True, "viewer": False, "editor": False},
                    "developer": {"admin": True, "viewer": False, "editor": False},
                }
            },
            prefix="admin_runtime_pylons_",
            icon_class="fas fa-server fa-fw",
        )
        #
        # Migration
        #
        theme.register_mode_section(
            "administration", "migration", "Migration",
            kind="holder",
            permissions={
                "permissions": ["migration"],
                "recommended_roles": {
                    "administration": {"admin": True, "viewer": False, "editor": False},
                    "default": {"admin": True, "viewer": False, "editor": False},
                    "developer": {"admin": True, "viewer": False, "editor": False},
                }
            },
            location="left",
            icon_class="fas fa-info-circle fa-fw",
        )
        theme.register_mode_subsection(
            "administration", "migration",
            "db", "DB",
            title="DB",
            kind="slot",
            permissions={
                "permissions": ["migration.db"],
                "recommended_roles": {
                    "administration": {"admin": True, "viewer": False, "editor": False},
                    "default": {"admin": True, "viewer": False, "editor": False},
                    "developer": {"admin": True, "viewer": False, "editor": False},
                }
            },
            prefix="admin_migration_db_",
            icon_class="fas fa-server fa-fw",
        )
        theme.register_mode_subsection(
            "administration", "migration",
            "permissions", "Permissions",
            title="Permissions",
            kind="slot",
            permissions={
                "permissions": ["migration.permissions"],
                "recommended_roles": {
                    "administration": {"admin": True, "viewer": False, "editor": False},
                    "default": {"admin": True, "viewer": False, "editor": False},
                    "developer": {"admin": True, "viewer": False, "editor": False},
                }
            },
            prefix="admin_migration_permissions_",
            icon_class="fas fa-server fa-fw",
        )
        #
        # Invites
        #
        theme.register_mode_section(
            "administration", "invites", "Invites",
            kind="holder",
            permissions={
                "permissions": ["invites"],
                "recommended_roles": {
                    "administration": {"admin": True, "viewer": False, "editor": False},
                    "default": {"admin": True, "viewer": False, "editor": False},
                    "developer": {"admin": True, "viewer": False, "editor": False},
                }
            },
            location="left",
            icon_class="fas fa-info-circle fa-fw",
        )
        theme.register_mode_subsection(
            "administration", "invites",
            "platform", "Platform",
            title="Platform",
            kind="slot",
            permissions={
                "permissions": ["invites.platform"],
                "recommended_roles": {
                    "administration": {"admin": True, "viewer": False, "editor": False},
                    "default": {"admin": True, "viewer": False, "editor": False},
                    "developer": {"admin": True, "viewer": False, "editor": False},
                }
            },
            prefix="admin_invites_platform_",
            icon_class="fas fa-server fa-fw",
        )
        theme.register_mode_subsection(
            "administration", "invites",
            "bulkusers", "Bulk users",
            title="Bulk users",
            kind="slot",
            permissions={
                "permissions": ["invites.bulkusers"],
                "recommended_roles": {
                    "administration": {"admin": True, "viewer": False, "editor": False},
                    "default": {"admin": True, "viewer": False, "editor": False},
                    "developer": {"admin": True, "viewer": False, "editor": False},
                }
            },
            prefix="admin_invites_bulkusers_",
            icon_class="fas fa-server fa-fw",
        )
        theme.register_mode_subsection(
            "administration", "invites",
            "bulkprojects", "Bulk projects",
            title="Bulk projects",
            kind="slot",
            permissions={
                "permissions": ["invites.bulkprojects"],
                "recommended_roles": {
                    "administration": {"admin": True, "viewer": False, "editor": False},
                    "default": {"admin": True, "viewer": False, "editor": False},
                    "developer": {"admin": True, "viewer": False, "editor": False},
                }
            },
            prefix="admin_invites_bulkprojects_",
            icon_class="fas fa-server fa-fw",
        )
        #
        # Users
        #
        theme.register_mode_section(
            "administration", "users", "Users",
            kind="holder",
            permissions={
                "permissions": ["admin.auth.users"],
                "recommended_roles": {
                    "administration": {"admin": True, "viewer": False, "editor": False},
                    "default": {"admin": True, "viewer": False, "editor": False},
                    "developer": {"admin": True, "viewer": False, "editor": False},
                }
            },
            location="left",
            icon_class="fas fa-info-circle fa-fw",
        )
        theme.register_mode_subsection(
            "administration", "users",
            "users", "Users",
            title="Users",
            kind="slot",
            permissions={
                "permissions": ["admin.auth.users"],
                "recommended_roles": {
                    "administration": {"admin": True, "viewer": False, "editor": False},
                    "default": {"admin": True, "viewer": False, "editor": False},
                    "developer": {"admin": True, "viewer": False, "editor": False},
                }
            },
            prefix="admin_auth_users_",
            icon_class="fas fa-server fa-fw",
        )
        # Init
        self.descriptor.init_all()
        #
        vault_client = VaultClient()  # for administration mode
        vault_client.create_project_space(quiet=True)
        #
        secrets = vault_client.get_all_secrets()
        if "auth_token" not in secrets:
            #
            try:
                system_user_id = self.context.rpc_manager.call.auth_get_user(
                    email="system@centry.user",
                )["id"]
            except:  # pylint: disable=W0702
                system_user_id = None
            #
            if system_user_id is not None:
                all_tokens = self.context.rpc_manager.call.auth_list_tokens(
                    system_user_id
                )
                #
                if len(all_tokens) < 1:
                    token_id = self.context.rpc_manager.call.auth_add_token(
                        system_user_id, "api",
                    )
                else:
                    token_id = all_tokens[0]["id"]
                #
                token = self.context.rpc_manager.call.auth_encode_token(token_id)
                #
                secrets["auth_token"] = token
                vault_client.set_secrets(secrets)

    def deinit(self):  # pylint: disable=R0201
        """ De-init module """
        log.info("De-initializing module")
        # De-init
        # self.descriptor.deinit_all()
