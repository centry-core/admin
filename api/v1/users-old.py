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

""" API """

import flask  # pylint: disable=E0401,W0611
import flask_restful  # pylint: disable=E0401

from pylon.core.tools import log  # pylint: disable=E0611,E0401,W0611

from tools import auth  # pylint: disable=E0401


class API(flask_restful.Resource):  # pylint: disable=R0903
    """
        API Resource

        Endpoint URL structure: <pylon_root>/api/<api_version>/<plugin_name>/<resource_name>

        Example:
        - Pylon root is at "https://example.com/"
        - Plugin name is "demo"
        - We are in subfolder "v1"
        - Current file name is "myapi.py"

        API URL: https://example.com/api/v1/demo/myapi

        API resources use check_api auth decorator
        auth.decorators.check_api takes the following arguments:
        - permissions
        - scope_id=1
        - access_denied_reply={"ok": False, "error": "access_denied"},
    """

    url_params = [
        '<int:project>',
    ]

    def __init__(self, module):
        self.module = module

    @auth.decorators.check_api(["global_admin"])
    def get(self, project):  # pylint: disable=R0201
        """ Process """
        #
        project_ids = [item["id"] for item in
                       self.module.context.rpc_manager.call.project_list()]
        if project not in project_ids:
            return {"total": 0, "rows": []}
        #
        project_scope_name = f"Project-{project}"
        scope_map = {item["name"]: item["id"] for item in auth.list_scopes()}
        #
        if project_scope_name not in scope_map:
            return {"total": 0, "rows": []}
        #
        project_scope_id = scope_map.get(project_scope_name)
        #
        all_users = auth.list_users()
        #
        project_users = list()
        for user in all_users:
            if user["name"].startswith(":Carrier:Project:"):
                continue
            #
            project_user_permissions = self.module.context.rpc_manager.call.auth_get_user_permissions(
                user["id"], project_scope_id
            )
            #
            if "project_member" in project_user_permissions:
                project_users.append(user)
        #
        return {
            "total": len(project_users),
            "rows": project_users,
        }

    @auth.decorators.check_api(["global_admin"])
    def post(self, project):  # pylint: disable=R0201
        """ Process """
        #
        data = flask.request.json
        user_name = data["name"]
        #
        project_ids = [item["id"] for item in
                       self.module.context.rpc_manager.call.project_list()]
        if project not in project_ids:
            return {}
        #
        project_scope_name = f"Project-{project}"
        scope_map = {item["name"]: item["id"] for item in auth.list_scopes()}
        #
        if project_scope_name not in scope_map:
            return {}
        #
        project_scope_id = scope_map.get(project_scope_name)
        #
        user_map = {item["name"]: item["id"] for item in auth.list_users()}
        if user_name not in user_map:
            return {}
        #
        user_id = user_map[user_name]
        #
        project_user_permissions = self.module.context.rpc_manager.call.auth_get_user_permissions(
            user_id, project_scope_id
        )
        if "project_member" not in project_user_permissions:
            self.module.context.rpc_manager.call.auth_add_user_permission(
                user_id, project_scope_id, "project_member"
            )
            log.info("Added permission for %s: %s", user_id, "project_member")
        #
        return {}
