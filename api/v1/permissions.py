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
from itertools import groupby

import flask  # pylint: disable=E0401,W0611
import flask_restful  # pylint: disable=E0401
from flask import g, request

from pylon.core.tools import log  # pylint: disable=E0611,E0401,W0611

from tools import auth  # pylint: disable=E0401


def group_roles_by_permissions(auth_permissions):
    roles_to_permissions = {}
    for key, group_items in groupby(auth_permissions, key=lambda x: x['name']):
        roles_to_permissions[key] = set()
        for item in group_items:
            roles_to_permissions[key].add(item['permission'])
    return roles_to_permissions


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

    def __init__(self, module):
        self.module = module

    @auth.decorators.check_api({
        "permissions": ["admin.roles.permissions.view"],
        "recommended_roles": {
            "administration": {"admin": True, "viewer": True, "editor": False},
            "project": {"admin": True, "viewer": True, "editor": False},
            "develop": {"admin": True, "viewer": False, "editor": False},
        }})
    def get(self):  # pylint: disable=R0201
        """ Process """
        roles = auth.get_roles()
        auth_permissions = auth.get_permissions()
        log.info(f"{roles=} {auth_permissions=}")
        local_permissions = auth.local_permissions

        permissions = set(auth.resolve_permissions(scope_id=1, auth_data=g.auth))
        all_permissions = local_permissions | permissions
        log.info(f"{permissions=} {local_permissions=} {all_permissions=}")
        roles_to_permissions = group_roles_by_permissions(auth_permissions)
        all_permissions = sorted(all_permissions)
        return {
            "total": len(all_permissions),
            "rows": [{
                "name": permission,
                **{role["name"]: permission in roles_to_permissions[role["name"]] for
                   role in roles}
            } for permission in all_permissions]
        }

    @auth.decorators.check_api({
        "permissions": ["admin.roles.permissions.edit"],
        "recommended_roles": {
            "administration": {"admin": True, "viewer": True, "editor": False},
            "project": {"admin": True, "viewer": True, "editor": False},
            "develop": {"admin": True, "viewer": False, "editor": False},
        }})
    def put(self):  # pylint: disable=R0201
        """ Process """
        new_data = request.get_json()
        old_data = self.get()["rows"]
        old_permissions = set(
            (r, p['name']) for p in old_data for r, v in p.items() if v)
        new_permissions = set(
            (r, p['name']) for p in new_data for r, v in p.items() if v)
        permissions_to_delete = old_permissions - new_permissions
        permissions_to_add = new_permissions - old_permissions
        for permission in permissions_to_add:
            auth.set_permission_for_role(*permission)
        for permission in permissions_to_delete:
            auth.remove_permission_from_role(*permission)
        return {"ok": True}
