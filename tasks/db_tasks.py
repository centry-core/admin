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

import time

from tools import context  # pylint: disable=E0401

from .logs import make_logger


def create_tables():
    """ Task """
    #
    with make_logger() as log:
        log.info("Starting")
        start_ts = time.time()
        #
        try:
            from tools import db  # pylint: disable=C0415,E0401
            #
            log.info("Getting shared metadata")
            shared_metadata = db.get_shared_metadata()
            #
            log.info("Applying shared metadata")
            with db.get_session(None) as shared_db:
                shared_metadata.create_all(bind=shared_db.connection())
                shared_db.commit()
            #
            log.info("Getting project metadata")
            tenant_metadata = db.get_tenant_specific_metadata()
            #
            log.info("Getting project list")
            project_list = context.rpc_manager.timeout(120).project_list(
                filter_={"create_success": True},
            )
            #
            for project in project_list:
                log.info("Applying project metadata: %s", project)
                with db.get_session(project["id"]) as tenant_db:
                    tenant_metadata.create_all(bind=tenant_db.connection())
                    tenant_db.commit()
        except:  # pylint: disable=W0702
            log.exception("Got exception, stopping")
        #
        end_ts = time.time()
        log.info("Exiting (duration = %s)", end_ts - start_ts)


def propose_migrations():
    """ Task """
    #
    with make_logger() as log:
        log.info("Starting")
        start_ts = time.time()
        #
        try:
            from tools import db  # pylint: disable=C0415,E0401
            #
            log.info("Getting shared metadata")
            shared_metadata = db.get_shared_metadata()
            #
            from alembic.migration import MigrationContext  # pylint: disable=C0415,E0401
            from alembic.autogenerate import compare_metadata  # pylint: disable=C0415,E0401
            #
            log.info("Comparing shared metadata")
            with db.get_session(None) as shared_db:
                migration_ctx = MigrationContext.configure(
                    connection=shared_db.connection(),
                )
                #
                db_diff = compare_metadata(migration_ctx, shared_metadata)
                #
                log.info("DB diff: %s", db_diff)
        except:  # pylint: disable=W0702
            log.exception("Got exception, stopping")
        #
        end_ts = time.time()
        log.info("Exiting (duration = %s)", end_ts - start_ts)
