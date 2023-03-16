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
from flask import g, request

from pylon.core.tools import log  # pylint: disable=E0611,E0401,W0611

from tools import auth  # pylint: disable=E0401


class API(flask_restful.Resource):  # pylint: disable=R0903
    url_params = [
        "<string:mode>"
    ]

    def __init__(self, module):
        self.module = module

    def get(self, mode):
        roles = auth.get_roles(mode)
        return roles

    def post(self, mode):  # pylint: disable=R0201
        """ Process """
        role_name = request.json["name"]
        auth.add_role(role_name, mode)
        return {"ok": True}

    def delete(self, mode):
        role_name = request.json["name"]
        auth.delete_role(role_name, mode)
        return {"ok": True}

    def put(self, mode):
        name, new_name = request.json["name"], request.json["new_name"]
        auth.update_role_name(name, new_name, mode)
        return {"ok": True}

# user | project_id

# user | role | mode | project_id (optional)

# permission | role | mode
