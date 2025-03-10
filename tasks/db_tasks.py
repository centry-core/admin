#!/usr/bin/python3
# coding=utf-8

#   Copyright 2025 getcarrier.io
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

""" Task """

from tools import context  # pylint: disable=E0401

from .logs import make_logger


def create_tables():
    """ Task """
    #
    with make_logger() as log:
        log.info("Starting")
        #
        try:
            project_list = context.rpc_manager.timeout(120).project_list(
                filter_={"create_success": True},
            )
            #
            from tools import db  # pylint: disable=C0415,E0401
            #
            for project in project_list:
                log.info("Init project DB: Project %s", project)
                #
                with db.get_session(project["id"]) as tenant_db:
                    log.info("- Getting metadata")
                    metadata = db.get_all_metadata()
                    #
                    log.info("- Creating tables")
                    metadata.create_all(bind=tenant_db.connection())
                    #
                    log.info("- DB commit")
                    tenant_db.commit()
        except:  # pylint: disable=W0702
            log.exception("Got exception, stopping")


def propose_migrations():
    """ Task """
    #
    with make_logger() as log:
        log.info("Starting")
