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
from flask import g

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

    def __init__(self, module):
        self.module = module

    @auth.decorators.check_api(["global_admin"])
    def get(self):  # pylint: disable=R0201
        """ Process """
        roles = self.module.context.rpc_manager.call.get_roles()
        local_permissions = set()
        permissions = set(auth.resolve_permissions(scope_id=1, auth_data=g.auth))
        permissions = {'performance.backend.tests.delete', 'performance.backend.tests',
                       'performance.backend', 'performance.backend.tests.view',
                       'performance.backend.tests.edit', 'performance.backend.tests.create',
                       'performance'}
        all_permissions = local_permissions | permissions
        # log.info(f"{permissions=} {local_permissions=} {all_permissions=}")
        return {
            "total": len(all_permissions),
            "rows": [{
                "name": permission,
                "roles": {role: True for role in roles},
            } for permission in all_permissions],
        }
