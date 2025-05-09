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


def create_tables(*args, **kwargs):
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


def propose_migrations(*args, **kwargs):  # pylint: disable=R0914
    """ Task """
    #
    with make_logger() as log:
        log.info("Starting")
        start_ts = time.time()
        #
        try:
            from tools import db  # pylint: disable=C0415,E0401
            from tools import config as c  # pylint: disable=C0415,E0401
            #
            from sqlalchemy import MetaData  # pylint: disable=C0415,E0401
            #
            from alembic.migration import MigrationContext  # pylint: disable=C0415,E0401
            from alembic.autogenerate import compare_metadata, produce_migrations, render_op_text  # pylint: disable=C0415,E0401
            from alembic.autogenerate.api import AutogenContext  # pylint: disable=C0415,E0401
            #
            # ---
            #
            log.info("Getting shared metadata")
            shared_metadata = db.get_shared_metadata()
            #
            log.info("Comparing shared metadata")
            with db.get_session(None) as shared_db:
                def _non_auth_name(name, type_, parent_names):  # pylint: disable=W0613
                    if name is not None:
                        return "auth_core" not in name
                    #
                    return True
                #
                migration_ctx = MigrationContext.configure(
                    connection=shared_db.connection(),
                    opts={
                        "include_name": _non_auth_name,
                    },
                )
                #
                db_diffs = compare_metadata(migration_ctx, shared_metadata)
                #
                for db_diff in db_diffs:
                    log.info("- Shared DB diff: %s", db_diff)
                #
                db_script = produce_migrations(migration_ctx, shared_metadata)
                autogen_context = AutogenContext(migration_ctx, metadata=shared_metadata)
                #
                for upgrade_op in db_script.upgrade_ops.ops:
                    rendered_op = render_op_text(autogen_context, upgrade_op)
                    log.info("- - Shared DB op: %s", rendered_op)
            #
            # ---
            #
            def _get_tenant_specific_metadata(target_schema):
                meta = MetaData(schema=target_schema)
                for table in db.Base.metadata.tables.values():
                    if table.schema == c.POSTGRES_TENANT_SCHEMA:
                        table.tometadata(meta, schema=target_schema)
                return meta
            #
            log.info("Getting project list")
            project_list = context.rpc_manager.timeout(120).project_list(
                filter_={"create_success": True},
            )
            #
            if project_list:
                project = project_list[0]
                #
                log.info("Processing project: %s", project)
                with db.get_session(project["id"]) as tenant_db:
                    from tools import project_constants as pc  # pylint: disable=E0401,C0415
                    project_schema = pc["PROJECT_SCHEMA_TEMPLATE"].format(project["id"])
                    #
                    log.info("Getting project metadata")
                    tenant_metadata = _get_tenant_specific_metadata(project_schema)
                    #
                    # Shoud fix key -> table relation after such changes
                    # for table in tenant_metadata.sorted_tables:
                    #     table.schema = project_schema
                    #
                    def _project_schema_name(name, type_, parent_names):  # pylint: disable=W0613
                        if type_ == "schema":
                            return name == project_schema
                        #
                        return True
                    #
                    migration_ctx = MigrationContext.configure(
                        connection=tenant_db.connection(),
                        opts={
                            "include_schemas": True,
                            "include_name": _project_schema_name,
                        },
                    )
                    #
                    log.info("Comparing project metadata")
                    db_diffs = compare_metadata(migration_ctx, tenant_metadata)
                    #
                    for db_diff in db_diffs:
                        log.info("- Project DB diff: %s", db_diff)
            #
        except:  # pylint: disable=W0702
            log.exception("Got exception, stopping")
        #
        end_ts = time.time()
        log.info("Exiting (duration = %s)", end_ts - start_ts)
