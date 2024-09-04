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

from pylon.core.tools import log  # pylint: disable=E0611,E0401,W0611

from tools import auth  # pylint: disable=E0401
from tools import api_tools  # pylint: disable=E0401


class AdminAPI(api_tools.APIModeHandler):  # pylint: disable=R0903
    """ API """

    @auth.decorators.check_api(["modes.users"])
    def post(self):
        """ Process POST """
        data = flask.request.get_json()
        #
        if "user_name" not in data or not data["user_name"]:
            return {
                "ok": False,
                "error": "Name not set",
            }
        #
        if "user_email" not in data or not data["user_email"]:
            return {
                "ok": False,
                "error": "Email not set",
            }
        #
        try:
            invite = self.module.context.rpc_manager.timeout(5).auth_cirro_invite(
                email=data["user_email"],
                name=data["user_name"],
            )
            #
            log.debug("Invite: %s", invite)
        except BaseException as ex:  # pylint: disable=W0718
            return {
                "ok": False,
                "error": str(ex),
            }
        #
        return {"ok": True}


class API(api_tools.APIBase):  # pylint: disable=R0903
    """ API """

    url_params = [
        "<string:mode>",
    ]

    mode_handlers = {
        'administration': AdminAPI,
    }
