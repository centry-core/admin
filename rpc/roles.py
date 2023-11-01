from collections import defaultdict
from typing import Optional

from flask import g

from tools import rpc_tools, db, db_tools

from sqlalchemy.exc import NoResultFound, ProgrammingError
from ..models.users import User, Role, UserRole, RolePermission
from pylon.core.tools import web, log

PROJECT_ROLE_NAME = 'default'


class RPC:

    @web.rpc("admin_get_roles", "get_roles")
    def get_roles(self, project_id: int, **kwargs) -> list[dict]:
        with db.with_project_schema_session(project_id) as tenant_session:
            roles = tenant_session.query(Role).all()
            roles = [role.to_json() for role in roles]
            return roles

    @web.rpc("admin_add_role", "add_role")
    def add_role(self, project_id: int, role_names: list[str], **kwargs) -> dict:
        with db.with_project_schema_session(project_id) as tenant_session:
            for role_name in role_names:
                role = Role(name=role_name)
                tenant_session.add(role)
            tenant_session.commit()
            return role.to_json()

    @web.rpc("admin_delete_role", "delete_role")
    def delete_role(self, project_id: int, role_name: str, **kwargs) -> bool:
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

    @web.rpc("admin_update_role_name", "update_role_name")
    def update_role_name(self, project_id: int, role_name: str, new_role_name: str, **kwargs) -> bool:
        with db.with_project_schema_session(project_id) as tenant_session:
            role = tenant_session.query(Role).filter(Role.name == role_name).first()
            if role:
                role.name = new_role_name
                tenant_session.commit()
            return True

    @web.rpc("admin_get_permissions", "get_permissions")
    def get_permissions(self, project_id: int, **kwargs) -> list[dict]:
        with db.with_project_schema_session(project_id) as tenant_session:
            permissions = tenant_session.query(RolePermission, Role).filter(
                RolePermission.role_id == Role.id).all()
            return [{
                "name": role.name,
                "permission": permission.permission,
            } for permission, role in permissions]

    @web.rpc("admin_set_permission_for_role", "set_permission_for_role")
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

    @web.rpc("admin_remove_permission_from_role", "remove_permission_from_role")
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

    @web.rpc("admin_add_user_to_project", "add_user_to_project")
    def add_user_to_project(self, project_id: int, user_id: int, role_names: list[str], **kwargs) -> bool:
        with db.with_project_schema_session(project_id) as tenant_session:
            user = tenant_session.query(User).filter(User.auth_id == user_id).first()
            if not user:
                user = User(auth_id=user_id)
                tenant_session.add(user)
            roles = tenant_session.query(Role).filter(Role.name.in_(role_names)).all()
            for role in roles:
                user_role = UserRole(user_id=user.id, role_id=role.id)
                tenant_session.add(user_role)
            tenant_session.commit()
            return True

    @web.rpc("admin_remove_users_from_project", "remove_users_from_project")
    def remove_users_from_project(self, project_id: int, user_ids: list[int], **kwargs) -> bool:
        with db.with_project_schema_session(project_id) as tenant_session:
            tenant_session.query(UserRole).filter(
                UserRole.user_id.in_(user_ids)).delete()
            tenant_session.query(User).filter(
                User.auth_id.in_(user_ids)).delete()
            tenant_session.commit()
            return True

    @web.rpc("admin_get_permissions_in_project", "get_permissions_in_project")
    def get_permissions_in_project(self, project_id: int, user_id: int, **kwargs) -> set[str]:
        # log.info('get_permissions_in_project, p: %s, u: %s', project_id, user_id)
        try:
            with db.with_project_schema_session(project_id) as tenant_session:
                user = tenant_session.query(User).filter(User.auth_id == user_id).first()
                if user:
                    permissions = tenant_session.query(UserRole, RolePermission).filter(
                        UserRole.user_id == user.id,
                        RolePermission.role_id == UserRole.role_id,
                    ).all()
                    permissions = {permission.permission for _, permission in permissions}
                    return permissions
        except ProgrammingError:
            # this happens if project schema is deleted. We need to clear session then

            ...
        return set()

    @web.rpc("admin_get_users_ids_in_project", "get_users_ids_in_project")
    def get_users_ids_in_project(self, project_id: int, **kwargs) -> list[dict]:
        with db.with_project_schema_session(project_id) as tenant_session:
            users = tenant_session.query(User).all()
            users = [user.to_json() for user in users]
            return users

    @web.rpc("admin_get_users_roles_in_project", "get_users_roles_in_project")
    def get_users_roles_in_project(self, project_id: int, filter_system_user: bool = False, **kwargs) -> dict[list]:
        filter_ = [
            User.id == UserRole.user_id,
            Role.id == UserRole.role_id
        ]
        if filter_system_user:
            system_user = self.get_project_system_user(project_id)
            if system_user:
                filter_.append(User.auth_id != system_user['id'])
        with db.with_project_schema_session(project_id) as tenant_session:
            query = tenant_session.query(User, UserRole, Role).filter(*filter_)
            users = query.all()

        user_roles = defaultdict(list)
        for user, _, role in users:
            user_roles[user.auth_id].append(role.name)
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

    @web.rpc("admin_get_user_roles", "get_user_roles")
    def get_user_roles(self, project_id, user_id) -> list[dict]:
        with db.with_project_schema_session(project_id) as tenant_session:
            user = tenant_session.query(User).filter(User.auth_id == user_id).first()
            if user:
                user_roles = tenant_session.query(UserRole).with_entities(UserRole.role_id).filter(
                    UserRole.user_id == user.id).all()
                user_roles = [role[0] for role in user_roles]
                roles = tenant_session.query(Role).filter(Role.id.in_(user_roles)).all()
                return [role.to_json() for role in roles]
            return []

    @web.rpc('admin_check_user_in_project', 'check_user_in_project')
    def check_user_in_project(self, project_id: int, user_id: Optional[int] = None, **kwargs) -> bool:
        # log.info('Checking if user %s is in project %s', user_id, project_id)
        if not user_id:
            log.info('User is None. Trying to get user from flask.g ...')
            try:
                user_id = int(g.auth.id)
            except (AttributeError, TypeError, ValueError):
                return False
        log.info('Checking if user %s is in project %s', user_id, project_id)

        try:
            with db.with_project_schema_session(project_id) as tenant_session:
                user = tenant_session.query(User).filter(User.auth_id == user_id).first()
                return bool(user)
        except ProgrammingError:
            # if project schema does not exist
            return False

    @web.rpc('admin_get_project_system_user', 'get_project_system_user')
    def check_user_in_project(self, project_id: int, **kwargs) -> Optional[dict]:
        from tools import auth, project_constants as pc
        try:
            return auth.get_user(email=pc['PROJECT_USER_EMAIL_TEMPLATE'].format(project_id))
        except (NoResultFound, RuntimeError):
            ...
        return
