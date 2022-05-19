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

# import sqlalchemy  # pylint: disable=E0401

from pylon.core.tools import log  # pylint: disable=E0401
from pylon.core.tools import module  # pylint: disable=E0401
from pylon.core.tools.context import Context as Holder  # pylint: disable=E0401

from tools import theme  # pylint: disable=E0401
from tools import db  # pylint: disable=E0401
from tools import db_migrations  # pylint: disable=E0401

# from .db import init_db


class Module(module.ModuleModel):
    """ Pylon module """

    def __init__(self, context, descriptor):
        self.context = context
        self.descriptor = descriptor
        #
        # self.db = Holder()  # pylint: disable=C0103
        # self.db.tbl = Holder()

    def init(self):
        """ Init module """
        log.info("Initializing module")
        # Run DB migrations
        # db_migrations.run_db_migrations(self, db.url)
        # DB
        # init_db(self)
        # Theme registration
        theme.register_section(
            "admin", "Administration",
            kind="holder",
            location="left",
            permissions=["global_admin"],
            icon_class="fas fa-info-circle fa-fw",
        )
        theme.register_subsection(
            "admin",
            "projects", "Projects",
            title="Projects",
            kind="slot",
            permissions=["global_admin"],
            prefix="admin_projects_",
            # icon_class="fas fa-server fa-fw",
            # weight=2,
        )
        theme.register_page(
            "admin", "projects", "edit",
            title="Edit",
            kind="slot",
            permissions=["global_admin"],
            prefix="admin_project_edit_",
        )
        theme.register_page(
            "admin", "projects", "empty",
            title="Empty",
            kind="slot",
            prefix="admin_empty_",
        )
        theme.register_landing(
            kind="route",
            route="admin.landing",
        )
        # Init RPCs
        self.descriptor.init_rpcs()
        # Init API
        self.descriptor.init_api()
        # Init SocketIO
        self.descriptor.init_sio()
        # Init blueprint
        self.descriptor.init_blueprint()
        # Init slots
        self.descriptor.init_slots()

    def deinit(self):  # pylint: disable=R0201
        """ De-init module """
        log.info("De-initializing module")
        # De-init slots
        # self.descriptor.deinit_slots()
        # De-init blueprint
        # self.descriptor.deinit_blueprint()
        # De-init SocketIO
        # self.descriptor.deinit_sio()
        # De-init API
        # self.descriptor.deinit_api()
        # De-init RPCs
        # self.descriptor.deinit_rpcs()
