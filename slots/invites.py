#!/usr/bin/python3
# coding=utf-8

#   Copyright 2024 getcarrier.io
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

""" Slot """

# from pylon.core.tools import log  # pylint: disable=E0611,E0401
from pylon.core.tools import web  # pylint: disable=E0611,E0401

from tools import auth  # pylint: disable=E0401
from tools import theme  # pylint: disable=E0401


class Slot:  # pylint: disable=E1101,R0903
    """
        Slot Resource

        self is pointing to current Module instance

        web.slot decorator takes one argument: slot name
        Note: web.slot decorator must be the last decorator (at top)

        Slot resources use check_slot auth decorator
        auth.decorators.check_slot takes the following arguments:
        - permissions
        - scope_id=1
        - access_denied_reply=None -> can be set to content to return in case of 'access denied'

    """

    @web.slot("admin_invites_platform_scripts")
    @auth.decorators.check_slot(
        ["invites.platform"],
        access_denied_reply=theme.access_denied_part,
    )
    def _invites_platform_scripts(self, context, slot, payload):
        _ = slot, payload
        #
        with context.app.app_context():
            return self.descriptor.render_template(
                "invites/platform_scripts.html",
            )

    @web.slot("admin_invites_bulkusers_scripts")
    @auth.decorators.check_slot(
        ["invites.bulkusers"],
        access_denied_reply=theme.access_denied_part,
    )
    def _invites_bulkusers_scripts(self, context, slot, payload):
        _ = slot, payload
        #
        with context.app.app_context():
            return self.descriptor.render_template(
                "invites/bulkusers_scripts.html",
            )

    @web.slot("admin_invites_bulkprojects_scripts")
    @auth.decorators.check_slot(
        ["invites.bulkprojects"],
        access_denied_reply=theme.access_denied_part,
    )
    def _invites_bulkprojects_scripts(self, context, slot, payload):
        _ = slot, payload
        #
        with context.app.app_context():
            return self.descriptor.render_template(
                "invites/bulkprojects_scripts.html",
            )
