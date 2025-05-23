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

""" Task to apply migrations 

This module provides functionality to apply auto-generated migrations to multiple project schemas.
It scans through all projects and applies necessary schema changes based on the comparison
between the current database state and the defined model structure.

To use this task:
1. Go to Admin -> Tasks
2. Select "apply_migrations" from the dropdown
3. Options for the parameter field:
   - Leave empty to migrate all projects (shared + all project schemas)
   - Enter a project ID to migrate only that specific project
   - Enter "shared" to migrate only the shared schema
4. Click "Start task"

The task will:
- Apply shared migrations first (affecting shared tables)
- Then apply project-specific migrations one by one
- Log all changes made to the database

"""

import io
import time

from tools import context  # pylint: disable=E0401

from .logs import make_logger


def apply_migrations(*args, **kwargs):  # pylint: disable=R0914
    """ Task to apply auto-generated migrations to multiple project schemas """
    #
    with make_logger() as log:
        log.info("Starting migration application")
        start_ts = time.time()
        #
        try:
            from tools import db  # pylint: disable=C0415,E0401
            from tools import config as c  # pylint: disable=C0415,E0401
            #
            from sqlalchemy import MetaData, text  # pylint: disable=C0415,E0401
            #
            from alembic.migration import MigrationContext  # pylint: disable=C0415,E0401
            from alembic.autogenerate import compare_metadata, produce_migrations  # pylint: disable=C0415,E0401
            from alembic.operations import Operations  # pylint: disable=C0415,E0401
            #
            # Check if a specific project was requested
            specific_project = kwargs.get("param")
            if specific_project:
                log.info("Working with specific project: %s", specific_project)
            
            # --- Apply shared migrations first ---
            #
            log.info("Getting shared metadata")
            shared_metadata = db.get_shared_metadata()
            #
            # Only apply shared migrations if no specific project is specified or if specifically requested
            if not specific_project or specific_project.lower() == "shared":
                log.info("Applying shared metadata migrations")
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
                    if not db_diffs:
                        log.info("No shared DB migrations needed")
                    else:
                        log.info("Found %d shared DB migrations to apply", len(db_diffs))
                        for db_diff in db_diffs:
                            log.info("- Shared DB diff: %s", db_diff)
                        #
                        db_script = produce_migrations(migration_ctx, shared_metadata)
                        # Apply the migrations directly to the database
                        operations = Operations(migration_ctx)
                        #
                        to_process = [db_script.upgrade_ops]
                        #
                        while to_process:
                            current_op = to_process.pop(0)
                            #
                            if hasattr(current_op, "ops"):
                                to_process.extend(current_op.ops)
                                continue
                            #
                            operations.invoke(current_op)
                        #
                        shared_db.commit()
                        log.info("Successfully applied shared DB migrations")
            elif specific_project.lower() == "shared":
                log.info("Skipping project-specific migrations as requested")
                return
            
            # --- Apply project-specific migrations ---
            #
            def _get_tenant_specific_metadata(target_schema):
                meta = MetaData(schema=target_schema)
                for table in db.Base.metadata.tables.values():
                    if table.schema == c.POSTGRES_TENANT_SCHEMA:
                        table.tometadata(meta, schema=target_schema)
                return meta
            #
            # If a specific project ID is provided, filter to just that project
            if specific_project and specific_project.lower() != "shared":
                log.info("Getting specific project: %s", specific_project)
                project_list = [{"id": specific_project}]
            else:
                log.info("Getting project list")
                project_list = context.rpc_manager.timeout(120).project_list(
                    filter_={"create_success": True},
                )
            #
            for project in project_list:
                log.info("Processing project migrations: %s", project)
                with db.get_session(project["id"]) as tenant_db:
                    from tools import project_constants as pc  # pylint: disable=E0401,C0415
                    project_schema = pc["PROJECT_SCHEMA_TEMPLATE"].format(project["id"])
                    #
                    log.info("Getting project metadata")
                    tenant_metadata = _get_tenant_specific_metadata(project_schema)
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
                    if not db_diffs:
                        log.info("No migrations needed for project %s", project["id"])
                        continue
                    #
                    log.info("Found %d migrations to apply for project %s", len(db_diffs), project["id"])
                    for db_diff in db_diffs:
                        log.info("- Project %s DB diff: %s", project["id"], db_diff)
                    #
                    db_script = produce_migrations(migration_ctx, tenant_metadata)
                    #
                    # Apply the migrations directly to the database
                    operations = Operations(migration_ctx)
                    #
                    to_process = [db_script.upgrade_ops]
                    #
                    while to_process:
                        current_op = to_process.pop(0)
                        #
                        if hasattr(current_op, "ops"):
                            to_process.extend(current_op.ops)
                            continue
                        #
                        operations.invoke(current_op)
                    #
                    tenant_db.commit()
                    log.info("Successfully applied migrations for project %s", project["id"])
            #
            log.info("All migrations applied successfully")
        except:  # pylint: disable=W0702
            log.exception("Got exception during migration, stopping")
        #
        end_ts = time.time()
        log.info("Exiting (duration = %s)", end_ts - start_ts)
