# Database Management System

This system provides functionality for managing database schemas and data across multiple projects in a multi-tenant environment.

## Overview

### Schema Management Tasks

1. **create_tables** - Creates all tables in shared and project-specific schemas
2. **propose_migrations** - Generates SQL migration scripts by comparing model definitions with existing database schemas
3. **apply_migrations** - Applies auto-generated migrations to the database (both shared and project-specific schemas)

### Backup & Restore Tasks

4. **backup_database** - Creates backups of database schemas (shared and/or project-specific)
5. **restore_database** - Restores database schemas from previously created backups
6. **list_backups** - Lists available database backups

## How It Works

### Architecture

- **Shared Schema**: Contains tables shared across all projects
- **Project Schemas**: Each project has its own schema with project-specific tables

### Migration Process

1. **Detect Changes**: The system uses Alembic to compare the current database schema with the model definitions
2. **Generate Migrations**: SQL migrations are auto-generated based on detected differences
3. **Apply Migrations**: Changes are applied directly to the database

## Usage

### Via Admin UI

1. Go to **Admin -> Tasks**
2. Select the desired task from the dropdown or use one of the convenience buttons

#### Schema Management
   - **Create Tables** - creates tables from scratch
   - **Propose Migrations** - generates but doesn't apply migrations
   - **Apply Migrations** - applies migrations to all projects

#### Backup & Restore
   - **List Backups** - lists all available database backups
   - **Backup Database** - creates a backup of the database
   - **Restore Database** - opens a dialog to restore from a backup

### Parameters

#### Schema Management Parameters:
- For **apply_migrations**, you can specify a project ID to migrate only that project
- Use "shared" as the parameter to only apply shared schema migrations

#### Backup Parameters:
- For **backup_database**, you can specify a project ID to backup only that project schema
- Use "shared" as the parameter to only backup the shared schema

#### Restore Parameters:
- For **restore_database**, specify the backup timestamp and optional schema specifier:
  - Format: `YYYYMMDD_HHMMSS[:schema]`
  - Examples: 
    - `20250520_123456` - restore all schemas from this backup
    - `20250520_123456:shared` - restore only the shared schema
    - `20250520_123456:project_123` - restore only a specific project schema

### Programmatically

You can also trigger database operations programmatically via the API:

```python
from tools import context

# Schema Management
context.rpc_manager.timeout(120).task_start("admin.task_node", "create_tables", {})
context.rpc_manager.timeout(120).task_start("admin.task_node", "propose_migrations", {})
context.rpc_manager.timeout(120).task_start("admin.task_node", "apply_migrations", {})

# Backup & Restore
context.rpc_manager.timeout(120).task_start("admin.task_node", "backup_database", {})
context.rpc_manager.timeout(120).task_start("admin.task_node", "list_backups", {})
context.rpc_manager.timeout(120).task_start("admin.task_node", "restore_database", 
    {"param": "20250520_123456:shared"})
```

## Best Practices

### Schema Management

1. Always run **propose_migrations** first to review the changes
2. Run migrations during maintenance windows or low-traffic periods
3. Back up your database before applying migrations
4. Review logs after migration to ensure all changes were applied correctly

### Backup & Restore

1. Create regular backups as part of your maintenance routine
2. Store backups in a secure location with appropriate retention policies
3. Test restore procedures periodically to ensure they work correctly
4. Use descriptive backup parameters to identify the content of backups
5. Always review the backup manifest before performing a restore operation

## Configuration

You can configure the backup directory by setting the `BACKUP_DIR` variable in your application config. The default is `/opt/carrier/backup`.

## Troubleshooting

If you encounter issues:

1. Check the task logs for detailed error messages
2. Verify that your model definitions are correct (for schema operations)
3. Ensure database connections have appropriate permissions
4. Verify that the backup directory exists and is writable
5. Check that the database user has sufficient privileges for backup/restore operations
