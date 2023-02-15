#!/usr/bin/python3
# coding=utf-8

#   Copyright 2023 getcarrier.io
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

""" Method """

import flask
from flask import g, request

from pylon.core.tools import log  # pylint: disable=E0611,E0401
from pylon.core.tools import web  # pylint: disable=E0611,E0401

from tools import auth  # pylint: disable=E0401


class Method:  # pylint: disable=E1101,R0903
    """
        Method Resource

        self is pointing to current Module instance

        web.method decorator takes zero or one argument: method name
        Note: web.method decorator must be the last decorator (at top)

    """

    @web.init()
    def _init(self):
        self.context.app.before_request(self.before_request_hook)

    @web.method("before_request_hook")
    def _before_request_hook(  # pylint: disable=R0913
            self,
    ):
        if flask.g.auth.id == "-":
            return
        #
        target_to_empty_or_needed = \
            ( \
                request.endpoint is not None and \
                request.endpoint.endswith(".static") \
            ) or \
            ( \
                request.endpoint == "api.v1.projects.project" \
            ) or \
            ( \
                request.endpoint == "api.v1.projects.session" \
            ) or \
            ( \
                request.path.endswith("/api/v1/projects/session") \
            ) or \
            ( \
                request.endpoint == "theme.route_section_subsection_page" and \
                request.view_args is not None and \
                request.view_args.get("section", "unknown") == "system" and \
                request.view_args.get("subsection", "unknown") == "status" and \
                request.view_args.get("page", "unknown") == "empty" \
            )
        #
        if target_to_empty_or_needed:
            return
        #
        user_projects = self.context.rpc_manager.call.list_user_projects(flask.g.auth.id)
        #
        if not user_projects:
            log.info("--- [REDIRECT] --- Request endpoint: %s", request.endpoint)
            log.info("--- [REDIRECT] --- Request view_args: %s", request.view_args)
            #
            return flask.redirect(
                flask.url_for(
                    "theme.route_section_subsection_page",
                    section="system", subsection="status", page="empty",
                )
            )
