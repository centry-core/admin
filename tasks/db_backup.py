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

""" 
Task to backup database schemas

This module provides functionality to backup database schemas (shared and project-specific).
It uses PostgreSQL's pg_dump utility to create backups of database schemas.

To use this task:
1. Go to Admin -> Tasks
2. Select "backup_database" from the dropdown
3. Options for the parameter field:
   - Leave empty to backup all schemas (shared + all project schemas)
   - Enter a project ID to backup only that specific project schema
   - Enter "shared" to backup only the shared schema
4. Click "Start task"

The task will:
- Create a timestamped backup file for each schema
- Compress the backup using gzip
- Store backups in the configured backup directory
- Log the backup process details

"""

import os
import time
import datetime
import subprocess
import json
import gzip
import shutil

from tools import context  # pylint: disable=E0401
from tools import config as c  # pylint: disable=E0401

from .logs import make_logger


# Configure backup location - can be overridden in config
DEFAULT_BACKUP_DIR = "/opt/carrier/backup"


def backup_database(*args, **kwargs):  # pylint: disable=R0914
    """ Task to backup database schemas """
    #
    with make_logger() as log:
        log.info("Starting database backup")
        start_ts = time.time()
        #
        try:
            from tools import db  # pylint: disable=C0415,E0401
            from tools import project_constants as pc  # pylint: disable=E0401,C0415
            #
            # Check if a specific project was requested
            specific_project = kwargs.get("param", "")
            if specific_project:
                log.info("Working with specific schema: %s", specific_project)
            
            # Get backup directory from config or use default
            backup_dir = getattr(c, "BACKUP_DIR", DEFAULT_BACKUP_DIR)
            
            # Create backup directory if it doesn't exist
            os.makedirs(backup_dir, exist_ok=True)
            
            # Generate timestamp for backup files
            timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
            
            # Get database connection parameters from config
            db_host = getattr(c, "POSTGRES_HOST", "postgres")
            db_port = getattr(c, "POSTGRES_PORT", "5432")
            db_name = getattr(c, "POSTGRES_DB", "carrier")
            db_user = getattr(c, "POSTGRES_USER", "carrier")
            db_password = getattr(c, "POSTGRES_PASSWORD", "carrier")
            
            # Set environment variable for password
            env = os.environ.copy()
            env["PGPASSWORD"] = db_password
            
            # Dictionary to track backup files
            backup_files = {}
            
            # Backup shared schema if needed
            if not specific_project or specific_project.lower() == "shared":
                shared_schema = getattr(c, "POSTGRES_SCHEMA", "public")
                log.info("Backing up shared schema: %s", shared_schema)
                
                # Build backup filename
                backup_filename = f"backup_{timestamp}_shared.sql"
                backup_filepath = os.path.join(backup_dir, backup_filename)
                
                # Build pg_dump command for shared schema
                cmd = [
                    "pg_dump",
                    f"--host={db_host}",
                    f"--port={db_port}",
                    f"--username={db_user}",
                    f"--dbname={db_name}",
                    f"--schema={shared_schema}",
                    "--format=plain",
                    "--no-owner",
                    "--no-acl",
                    f"--file={backup_filepath}"
                ]
                
                # Execute backup command
                log.info("Executing pg_dump command for shared schema")
                process = subprocess.run(
                    cmd,
                    env=env,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                    text=True,
                    check=False
                )
                
                if process.returncode == 0:
                    log.info("Shared schema backup completed successfully")
                    # Compress the backup file
                    with open(backup_filepath, 'rb') as f_in:
                        with gzip.open(f"{backup_filepath}.gz", 'wb') as f_out:
                            shutil.copyfileobj(f_in, f_out)
                    # Remove the uncompressed file
                    os.remove(backup_filepath)
                    # Update the filepath to the compressed file
                    backup_filepath = f"{backup_filepath}.gz"
                    backup_files["shared"] = {
                        "filename": f"{backup_filename}.gz",
                        "filepath": backup_filepath,
                        "timestamp": timestamp,
                        "size": os.path.getsize(backup_filepath)
                    }
                else:
                    log.error("Failed to backup shared schema: %s", process.stderr)
            
            # If we're only backing up the shared schema, we're done
            if specific_project and specific_project.lower() == "shared":
                log.info("Shared schema backup completed as requested")
            else:
                # Get all projects or the specific project
                if specific_project and specific_project.lower() != "shared":
                    log.info("Getting specific project: %s", specific_project)
                    project_list = [{"id": specific_project}]
                else:
                    log.info("Getting project list")
                    project_list = context.rpc_manager.timeout(120).project_list(
                        filter_={"create_success": True},
                    )
                
                # Backup each project schema
                for project in project_list:
                    project_id = project["id"]
                    project_schema = pc["PROJECT_SCHEMA_TEMPLATE"].format(project_id)
                    
                    log.info("Backing up project schema: %s", project_schema)
                    
                    # Build backup filename
                    backup_filename = f"backup_{timestamp}_project_{project_id}.sql"
                    backup_filepath = os.path.join(backup_dir, backup_filename)
                    
                    # Build pg_dump command for project schema
                    cmd = [
                        "pg_dump",
                        f"--host={db_host}",
                        f"--port={db_port}",
                        f"--username={db_user}",
                        f"--dbname={db_name}",
                        f"--schema={project_schema}",
                        "--format=plain",
                        "--no-owner",
                        "--no-acl",
                        f"--file={backup_filepath}"
                    ]
                    
                    # Execute backup command
                    log.info("Executing pg_dump command for project schema: %s", project_id)
                    process = subprocess.run(
                        cmd,
                        env=env,
                        stdout=subprocess.PIPE,
                        stderr=subprocess.PIPE,
                        text=True,
                        check=False
                    )
                    
                    if process.returncode == 0:
                        log.info("Project schema backup completed successfully: %s", project_id)
                        # Compress the backup file
                        with open(backup_filepath, 'rb') as f_in:
                            with gzip.open(f"{backup_filepath}.gz", 'wb') as f_out:
                                shutil.copyfileobj(f_in, f_out)
                        # Remove the uncompressed file
                        os.remove(backup_filepath)
                        # Update the filepath to the compressed file
                        backup_filepath = f"{backup_filepath}.gz"
                        backup_files[project_id] = {
                            "filename": f"{backup_filename}.gz",
                            "filepath": backup_filepath,
                            "timestamp": timestamp,
                            "size": os.path.getsize(backup_filepath)
                        }
                    else:
                        log.error("Failed to backup project schema %s: %s", project_id, process.stderr)
            
            # Create a backup manifest
            manifest_filepath = os.path.join(backup_dir, f"backup_manifest_{timestamp}.json")
            with open(manifest_filepath, 'w') as f:
                json.dump({
                    "timestamp": timestamp,
                    "backups": backup_files
                }, f, indent=2)
            
            log.info("Backup completed successfully. Manifest created at: %s", manifest_filepath)
            return {
                "status": "success",
                "timestamp": timestamp,
                "manifest": manifest_filepath,
                "backup_files": backup_files
            }
            
        except Exception as exc:  # pylint: disable=W0703
            log.exception("Got exception during backup: %s", str(exc))
            return {
                "status": "error",
                "error": str(exc)
            }
        finally:
            end_ts = time.time()
            log.info("Exiting (duration = %s)", end_ts - start_ts)
