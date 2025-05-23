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
Task to restore database schemas from backups

This module provides functionality to restore database schemas (shared and project-specific)
from previously created backups.

To use this task:
1. Go to Admin -> Tasks
2. Select "restore_database" from the dropdown
3. Options for the parameter field:
   - Enter the backup timestamp to restore (format: YYYYMMDD_HHMMSS)
   - Optionally add a schema specifier after the timestamp with a colon:
     - timestamp:shared - restore only shared schema
     - timestamp:project_id - restore only the specified project schema
     - timestamp:all - restore all schemas (default if no specifier provided)
4. Click "Start task"

The task will:
- Validate the backup files
- Restore the specified schemas
- Log the restoration process details

WARNING: Restoring a database will overwrite existing data. Always create a 
backup before performing a restore operation.
"""

import os
import time
import json
import subprocess
import gzip
import tempfile

from tools import context  # pylint: disable=E0401
from tools import config as c  # pylint: disable=E0401

from .logs import make_logger


# Configure backup location - can be overridden in config
DEFAULT_BACKUP_DIR = "/opt/carrier/backup"


def restore_database(*args, **kwargs):  # pylint: disable=R0914
    """ Task to restore database from backup """
    #
    with make_logger() as log:
        log.info("Starting database restore")
        start_ts = time.time()
        #
        try:
            from tools import db  # pylint: disable=C0415,E0401
            from tools import project_constants as pc  # pylint: disable=E0401,C0415
            #
            # Get parameter with backup timestamp and optional schema specifier
            param = kwargs.get("param", "")
            if not param:
                log.error("No backup timestamp provided")
                return {
                    "status": "error",
                    "error": "No backup timestamp provided. Format: YYYYMMDD_HHMMSS[:schema]"
                }
                
            # Parse parameter
            parts = param.split(":", 1)
            timestamp = parts[0]
            schema_specifier = parts[1] if len(parts) > 1 else "all"
            
            log.info("Restoring from backup with timestamp: %s, schema: %s", timestamp, schema_specifier)
            
            # Get backup directory from config or use default
            backup_dir = getattr(c, "BACKUP_DIR", DEFAULT_BACKUP_DIR)
            
            # Check if backup directory exists
            if not os.path.isdir(backup_dir):
                log.error("Backup directory does not exist: %s", backup_dir)
                return {
                    "status": "error",
                    "error": f"Backup directory not found: {backup_dir}"
                }
            
            # Look for the manifest file
            manifest_filepath = os.path.join(backup_dir, f"backup_manifest_{timestamp}.json")
            if not os.path.isfile(manifest_filepath):
                log.error("Backup manifest not found: %s", manifest_filepath)
                return {
                    "status": "error",
                    "error": f"Backup manifest not found: {manifest_filepath}"
                }
            
            # Load the manifest
            with open(manifest_filepath, 'r') as f:
                manifest = json.load(f)
            
            log.info("Loaded backup manifest: %s", manifest_filepath)
            
            # Get database connection parameters from config
            db_host = getattr(c, "POSTGRES_HOST", "postgres")
            db_port = getattr(c, "POSTGRES_PORT", "5432")
            db_name = getattr(c, "POSTGRES_DB", "carrier")
            db_user = getattr(c, "POSTGRES_USER", "carrier")
            db_password = getattr(c, "POSTGRES_PASSWORD", "carrier")
            
            # Set environment variable for password
            env = os.environ.copy()
            env["PGPASSWORD"] = db_password
            
            # Track restored schemas
            restored = []
            
            # Restore the shared schema if needed
            if schema_specifier.lower() == "all" or schema_specifier.lower() == "shared":
                if "shared" in manifest["backups"]:
                    shared_backup = manifest["backups"]["shared"]
                    log.info("Restoring shared schema from backup: %s", shared_backup["filename"])
                    
                    # Decompress the backup file to a temporary file
                    with tempfile.NamedTemporaryFile(delete=False, suffix='.sql') as temp_file:
                        temp_filepath = temp_file.name
                        with gzip.open(shared_backup["filepath"], 'rb') as f_in:
                            temp_file.write(f_in.read())
                    
                    # Build psql command to restore the shared schema
                    cmd = [
                        "psql",
                        f"--host={db_host}",
                        f"--port={db_port}",
                        f"--username={db_user}",
                        f"--dbname={db_name}",
                        "-v", "ON_ERROR_STOP=1",
                        "-f", temp_filepath
                    ]
                    
                    # Execute restore command
                    log.info("Executing psql command to restore shared schema")
                    process = subprocess.run(
                        cmd,
                        env=env,
                        stdout=subprocess.PIPE,
                        stderr=subprocess.PIPE,
                        text=True,
                        check=False
                    )
                    
                    # Clean up temporary file
                    os.unlink(temp_filepath)
                    
                    if process.returncode == 0:
                        log.info("Shared schema restore completed successfully")
                        restored.append("shared")
                    else:
                        log.error("Failed to restore shared schema: %s", process.stderr)
                        return {
                            "status": "error",
                            "error": f"Failed to restore shared schema: {process.stderr}"
                        }
                else:
                    log.warning("Shared schema backup not found in manifest")
            
            # If we're only restoring the shared schema, we're done
            if schema_specifier.lower() == "shared":
                log.info("Shared schema restore completed as requested")
            elif schema_specifier.lower() == "all":
                # Restore all project schemas
                for project_id, backup_info in manifest["backups"].items():
                    if project_id == "shared":
                        continue  # Already processed
                    
                    log.info("Restoring project schema for project: %s", project_id)
                    
                    # Decompress the backup file to a temporary file
                    with tempfile.NamedTemporaryFile(delete=False, suffix='.sql') as temp_file:
                        temp_filepath = temp_file.name
                        with gzip.open(backup_info["filepath"], 'rb') as f_in:
                            temp_file.write(f_in.read())
                    
                    # Build psql command to restore the project schema
                    cmd = [
                        "psql",
                        f"--host={db_host}",
                        f"--port={db_port}",
                        f"--username={db_user}",
                        f"--dbname={db_name}",
                        "-v", "ON_ERROR_STOP=1",
                        "-f", temp_filepath
                    ]
                    
                    # Execute restore command
                    log.info("Executing psql command to restore project schema: %s", project_id)
                    process = subprocess.run(
                        cmd,
                        env=env,
                        stdout=subprocess.PIPE,
                        stderr=subprocess.PIPE,
                        text=True,
                        check=False
                    )
                    
                    # Clean up temporary file
                    os.unlink(temp_filepath)
                    
                    if process.returncode == 0:
                        log.info("Project schema restore completed successfully: %s", project_id)
                        restored.append(project_id)
                    else:
                        log.error("Failed to restore project schema %s: %s", project_id, process.stderr)
            else:
                # Restore specific project schema
                project_id = schema_specifier
                if project_id in manifest["backups"]:
                    backup_info = manifest["backups"][project_id]
                    log.info("Restoring project schema for project: %s", project_id)
                    
                    # Decompress the backup file to a temporary file
                    with tempfile.NamedTemporaryFile(delete=False, suffix='.sql') as temp_file:
                        temp_filepath = temp_file.name
                        with gzip.open(backup_info["filepath"], 'rb') as f_in:
                            temp_file.write(f_in.read())
                    
                    # Build psql command to restore the project schema
                    cmd = [
                        "psql",
                        f"--host={db_host}",
                        f"--port={db_port}",
                        f"--username={db_user}",
                        f"--dbname={db_name}",
                        "-v", "ON_ERROR_STOP=1",
                        "-f", temp_filepath
                    ]
                    
                    # Execute restore command
                    log.info("Executing psql command to restore project schema: %s", project_id)
                    process = subprocess.run(
                        cmd,
                        env=env,
                        stdout=subprocess.PIPE,
                        stderr=subprocess.PIPE,
                        text=True,
                        check=False
                    )
                    
                    # Clean up temporary file
                    os.unlink(temp_filepath)
                    
                    if process.returncode == 0:
                        log.info("Project schema restore completed successfully: %s", project_id)
                        restored.append(project_id)
                    else:
                        log.error("Failed to restore project schema %s: %s", project_id, process.stderr)
                        return {
                            "status": "error",
                            "error": f"Failed to restore project schema {project_id}: {process.stderr}"
                        }
                else:
                    log.error("Project schema backup not found in manifest for project: %s", project_id)
                    return {
                        "status": "error",
                        "error": f"Project schema backup not found for project: {project_id}"
                    }
            
            log.info("Restore completed successfully. Restored schemas: %s", restored)
            return {
                "status": "success",
                "timestamp": timestamp,
                "restored_schemas": restored
            }
            
        except Exception as exc:  # pylint: disable=W0703
            log.exception("Got exception during restore: %s", str(exc))
            return {
                "status": "error",
                "error": str(exc)
            }
        finally:
            end_ts = time.time()
            log.info("Exiting (duration = %s)", end_ts - start_ts)
