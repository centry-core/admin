from pydantic import ValidationError

from tools import rpc_tools, db, db_tools
from ..models.users import User, Role, UserRole, RolePermission
from pylon.core.tools import web, log

PROJECT_ROLE_NAME = 'default'


class RPC:

    @web.rpc("get_roles", "admin_get_roles")
    def get_roles(self, project_id, **kwargs) -> list[str]:
        with db.with_project_schema_session(project_id) as tenant_session:
            roles = tenant_session.query(Role).all()
            roles = [role.to_json() for role in roles]
            return roles

    @web.rpc("add_role", "admin_add_role")
    def add_role(self, project_id, role_name, **kwargs) -> bool:
        with db.with_project_schema_session(project_id) as tenant_session:
            role = Role(name=role_name)
            tenant_session.add(role)
            tenant_session.commit()
        return True

    @web.rpc("delete_role", "admin_delete_role")
    def delete_role(self, project_id, role_name, **kwargs) -> bool:
        with db.with_project_schema_session(project_id) as tenant_session:
            role = tenant_session.query(Role).filter(Role.name == role_name).first()
            if role:
                role_permissions = tenant_session.query(RolePermission).filter(
                    RolePermission.role_id == role.id).all()
                for role_permission in role_permissions:
                    tenant_session.delete(role_permission)
                tenant_session.delete(role)
                tenant_session.commit()
            return True

    @web.rpc("update_role_name", "admin_update_role_name")
    def update_role_name(self, project_id, role_name, new_role_name, **kwargs) -> bool:
        with db.with_project_schema_session(project_id) as tenant_session:
            role = tenant_session.query(Role).filter(Role.name == role_name).first()
            if role:
                role.name = new_role_name
                tenant_session.commit()
            return True

    @web.rpc("get_permissions", "admin_get_permissions")
    def get_permissions(self, project_id, **kwargs) -> list[dict]:
        with db.with_project_schema_session(project_id) as tenant_session:
            permissions = tenant_session.query(RolePermission, Role).filter(
                RolePermission.role_id == Role.id).all()
            return [{
                "name": role.name,
                "permission": permission.permission,
            } for permission, role in permissions]

    @web.rpc("set_permission_for_role", "admin_set_permission_for_role")
    def set_permission_for_role(
            self, project_id: int, role_name: str, permission: str
    ) -> bool:
        with db.with_project_schema_session(project_id) as tenant_session:
            role = tenant_session.query(Role).filter(
                Role.name == role_name,
            ).first()
            if role:
                permission = RolePermission(role_id=role.id, permission=permission)
                tenant_session.add(permission)
                tenant_session.commit()
            return True

    @web.rpc("remove_permission_from_role", "admin_remove_permission_from_role")
    def remove_permission_from_role(
            self, project_id: int, role_name: str, permission: str
    ) -> bool:
        with db.with_project_schema_session(project_id) as tenant_session:
            role = tenant_session.query(Role).filter(
                Role.name == role_name,
            ).first()

            if role:
                permission = tenant_session.query(RolePermission).filter(
                    RolePermission.role_id == role.id).filter(
                    RolePermission.permission == permission).first()
                if permission:
                    tenant_session.delete(permission)
                    tenant_session.commit()
            return True

    @web.rpc("add_user_to_project", "admin_add_user_to_project")
    def add_user_to_project(self, project_id: int, user_id: int, role_name: str, **kwargs) -> bool:
        with db.with_project_schema_session(project_id) as tenant_session:
            user = tenant_session.query(User).filter(User.auth_id == user_id).first()
            if not user:
                user = User(auth_id=user_id)
                tenant_session.add(user)
            role = tenant_session.query(Role).filter(Role.name == role_name).first()
            if role:
                user_role = UserRole(user_id=user.id, role_id=role.id)
                tenant_session.add(user_role)
                tenant_session.commit()
            return True

    @web.rpc("remove_user_from_project", "admin_remove_user_from_project")
    def remove_user_from_project(self, project_id, user_id, **kwargs) -> bool:
        with db.with_project_schema_session(project_id) as tenant_session:
            user = tenant_session.query(User).filter(User.auth_id == user_id).first()
            if user:
                user_roles = tenant_session.query(UserRole).filter(
                    UserRole.user_id == user.id).all()
                for user_role in user_roles:
                    tenant_session.delete(user_role)
                tenant_session.commit()
            return True

    @web.rpc("get_permissions_in_project", "admin_get_permissions_in_project")
    def get_permissions_in_project(self, project_id, user_id, **kwargs) -> list[str]:
        with db.with_project_schema_session(project_id) as tenant_session:
            user = tenant_session.query(User).filter(User.auth_id == user_id).first()
            if user:
                permissions = tenant_session.query(UserRole, RolePermission).filter(
                    UserRole.user_id == user.id,
                    RolePermission.role_id == UserRole.role_id,
                ).all()
                permissions = [permission.permission for _, permission in permissions]
                return permissions
            return []

    @web.rpc("get_users_ids_in_project", "admin_get_users_ids_in_project")
    def get_users_ids_in_project(self, project_id, **kwargs) -> list[dict]:
        with db.with_project_schema_session(project_id) as tenant_session:
            users = tenant_session.query(User).all()
            users = [user.to_json() for user in users]
            return users

    @web.rpc("get_users_roles_in_project", "admin_get_users_roles_in_project")
    def get_users_roles_in_project(self, project_id, **kwargs) -> dict:
        with db.with_project_schema_session(project_id) as tenant_session:
            users = tenant_session.query(User, UserRole, Role).filter(
                User.id == UserRole.user_id,
                Role.id == UserRole.role_id
                ).all()
            user_roles = {}
            for user, _, role in users:
                user_roles.setdefault(user.auth_id, []).append(role.name)
            return user_roles

    @web.rpc("update_roles_for_user", "admin_update_roles_for_user")
    def update_roles_for_user(self, project_id, user_id, new_roles, **kwargs) -> bool:
        with db.with_project_schema_session(project_id) as tenant_session:
            user = tenant_session.query(User).filter(User.auth_id == user_id).first()
            if user:
                user_roles = tenant_session.query(UserRole).filter(
                    UserRole.user_id == user.id).all()
                for user_role in user_roles:
                    tenant_session.delete(user_role)
                for role_name in new_roles:
                    role = tenant_session.query(Role).filter(Role.name == role_name).first()
                    if role:
                        user_role = UserRole(user_id=user.id, role_id=role.id)
                        tenant_session.add(user_role)
                tenant_session.commit()
            return True
