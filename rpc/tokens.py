#!/usr/bin/python3
# coding=utf-8

#   Copyright 2025 EPAM Systems
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

""" RPC — auth token rotation """

from pylon.core.tools import log, web  # pylint: disable=E0611,E0401

from tools import auth, context, VaultClient  # pylint: disable=E0401


class RPC:

    @web.rpc("admin_rotate_tokens", "rotate_tokens")
    def rotate_tokens(self):
        """Rotate auth tokens for the admin space and all projects."""
        self._rotate_admin_token()
        self._rotate_project_tokens()

    # ------------------------------------------------------------------
    # Admin-level token
    # ------------------------------------------------------------------

    @web.rpc("admin_rotate_admin_token", "rotate_admin_token")
    def rotate_admin_token(self):
        """Rotate the admin-level auth_token (system@centry.user)."""
        self._rotate_admin_token()

    @staticmethod
    def _rotate_admin_token():
        try:
            system_user = auth.get_user(email="system@centry.user")
        except Exception:  # pylint: disable=W0703
            log.warning("Cannot rotate admin token: system user not found")
            return
        #
        user_id = system_user["id"]
        token_id = auth.add_token(user_id, "api")
        token = auth.encode_token(token_id)
        #
        vault_client = VaultClient()
        secrets = vault_client.get_secrets()
        secrets["auth_token"] = token
        vault_client.set_secrets(secrets)
        #
        log.info("Admin auth_token rotated")

    # ------------------------------------------------------------------
    # Per-project tokens
    # ------------------------------------------------------------------

    @web.rpc("admin_rotate_project_tokens", "rotate_project_tokens")
    def rotate_project_tokens(self):
        """Rotate auth tokens for all projects."""
        self._rotate_project_tokens()

    @staticmethod
    def _rotate_project_tokens():
        from plugins.projects.utils import get_project_user  # pylint: disable=E0401,C0415
        #
        project_list = context.rpc_manager.timeout(120).project_list(
            filter_={"create_success": True},
        )
        #
        for project in project_list:
            project_id = int(project["id"])
            #
            user = get_project_user(project_id)
            if user is None:
                log.warning("No system user for project %s, skipping", project_id)
                continue
            #
            user_id = user["id"]
            token_id = auth.add_token(user_id, "api")
            token = auth.encode_token(token_id)
            #
            vault_client = VaultClient(project_id)
            project_secrets = vault_client.get_secrets()
            project_secrets["auth_token"] = token
            vault_client.set_secrets(project_secrets)
            #
            log.info("Project %s auth_token rotated", project_id)
