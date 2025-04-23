from collections import defaultdict
from typing import Optional, List

from flask import g

from tools import rpc_tools, db, db_tools

from sqlalchemy.exc import NoResultFound, ProgrammingError
from sqlalchemy.sql.expression import (
    table,
    column,
    literal,
    select,
    union,
)
from ..models.pd.role import RoleDetailModel

from ..models.users import Role, UserRole, RolePermission
from pylon.core.tools import web, log

PROJECT_ROLE_NAME = 'default'


def set_permissions(session, role_name: str, permissions: List[str], commit: bool = True) -> None:
    role = session.query(Role).filter(
        Role.name == role_name,
    ).first()
    if role:
        for p in permissions:
            permission = RolePermission(role_id=role.id, permission=p)
            session.add(permission)
        if commit:
            session.commit()


class RPC:

    @web.rpc("admin_get_roles", "get_roles")
    def get_roles(self, project_id: int, **kwargs) -> list[dict]:
        with db.with_project_schema_session(project_id) as tenant_session:
            roles = tenant_session.query(Role).all()
            roles = [RoleDetailModel.from_orm(role).dict() for role in roles]
            return roles

    @web.rpc("admin_get_role", "get_role")
    def get_role(self, project_id: int, role_name: str, **kwargs) -> Optional[dict]:
        with db.with_project_schema_session(project_id) as tenant_session:
            role = tenant_session.query(Role).filter(Role.name == role_name).first()
            if role:
                return RoleDetailModel.from_orm(role).dict()
            return None

    @web.rpc("admin_add_role", "add_role")
    def add_role(self, project_id: int, role_names: list[str], **kwargs) -> dict:
        with db.with_project_schema_session(project_id) as tenant_session:
            for role_name in role_names:
                role = Role(name=role_name)
                tenant_session.add(role)
            tenant_session.commit()
            return RoleDetailModel.from_orm(role).dict()

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
    ) -> None:
        return self.set_permissions_for_role(
            project_id=project_id, role_name=role_name, permissions=[permission]
        )

    @web.rpc("admin_set_permissions_for_role", "set_permissions_for_role")
    def set_permissions_for_role(
            self, project_id: int, role_name: str, permissions: List[str],
            session=None, commit: bool = True
    ) -> None:
        if session:
            set_permissions(
                session=session,
                role_name=role_name,
                permissions=permissions,
                commit=False
            )
            if commit:
                session.commit()
        else:
            with db.get_session(project_id) as session:
                set_permissions(
                    session=session,
                    role_name=role_name,
                    permissions=permissions,
                    commit=False
                )
                if commit:
                    session.commit()

    @web.rpc("admin_get_permissions_for_role", "get_permissions_for_role")
    def get_permissions_for_role(
            self, project_id: int, role_name: str,
    ) -> List[str]:
        result = []
        #
        with db.with_project_schema_session(project_id) as tenant_session:
            role = tenant_session.query(Role).filter(
                Role.name == role_name,
            ).first()
            #
            if role:
                #
                permissions = tenant_session.query(RolePermission).filter(
                    RolePermission.role_id == role.id).all()
                #
                for perm in permissions:
                    result.append(perm.permission)
                #
                return result
        #
        return result

    @web.rpc("admin_add_permissions_for_role", "add_permissions_for_role")
    def add_permissions_for_role(
            self, project_id: int, role_name: str, permissions: List[str],
    ) -> bool:
        #
        with db.with_project_schema_session(project_id) as tenant_session:
            role = tenant_session.query(Role).filter(
                Role.name == role_name,
            ).first()
            #
            if role:
                #
                for perm in permissions:
                    permission = tenant_session.query(RolePermission).filter(
                        RolePermission.role_id == role.id).filter(
                        RolePermission.permission == perm).first()
                    #
                    if not permission:
                        permission = RolePermission(role_id=role.id, permission=perm)
                        tenant_session.add(permission)
                #
                tenant_session.commit()
                return True
        #
        return False

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
            roles = tenant_session.query(Role).filter(Role.name.in_(role_names)).all()
            for role in roles:
                user_role = UserRole(user_id=user_id, role_id=role.id)
                tenant_session.add(user_role)
            tenant_session.commit()
            return True

    @web.rpc("admin_remove_users_from_project", "remove_users_from_project")
    def remove_users_from_project(self, project_id: int, user_ids: list[int], **kwargs) -> bool:
        with db.with_project_schema_session(project_id) as tenant_session:
            tenant_session.query(UserRole).filter(
                UserRole.user_id.in_(user_ids)).delete()
            tenant_session.commit()
            return True

    @web.rpc("admin_get_permissions_in_project", "get_permissions_in_project")
    def get_permissions_in_project(self, project_id: int, user_id: int, **kwargs) -> set[str]:
        # log.info('get_permissions_in_project, p: %s, u: %s', project_id, user_id)
        try:
            with db.with_project_schema_session(project_id) as tenant_session:
                permissions = tenant_session.query(UserRole, RolePermission).filter(
                    UserRole.user_id == user_id,
                    RolePermission.role_id == UserRole.role_id,
                ).all()
                permissions = {permission.permission for _, permission in permissions}
                return permissions
        except ProgrammingError:
            # this happens if project schema is deleted. We need to clear session then

            ...
        return set()

    @web.rpc("admin_get_users_ids_in_project", "get_users_ids_in_project")
    def get_users_ids_in_project(self, project_id: int, filter_system_user: bool = False, **kwargs) -> list[int]:
        system_user_id = None
        if filter_system_user:
            system_user = self.get_project_system_user(project_id)
            if system_user:
                system_user_id = int(system_user['id'])
        with db.get_session(project_id) as session:
            q = session.query(UserRole.user_id).distinct()
            if system_user_id:
                q = q.where(UserRole.user_id != system_user_id)
            users = q.all()
            return [i[0] for i in users]

    @web.rpc("admin_get_users_roles_in_project", "get_users_roles_in_project")
    def get_users_roles_in_project(self, project_id: int, filter_system_user: bool = False, **kwargs) -> dict[list]:
        filter_ = [
            Role.id == UserRole.role_id
        ]
        if filter_system_user:
            system_user = self.get_project_system_user(project_id)
            if system_user:
                filter_.append(UserRole.user_id != system_user['id'])
        with db.with_project_schema_session(project_id) as tenant_session:
            query = tenant_session.query(UserRole, Role).filter(*filter_)
            users = query.all()

        user_roles = defaultdict(list)
        for user_role, role in users:
            user_roles[user_role.user_id].append(role.name)
        return user_roles

    @web.rpc("update_roles_for_user", "admin_update_roles_for_user")
    def update_roles_for_user(self, project_id: int, user_ids: List[int], new_roles: List[str], **kwargs) -> bool:
        with db.with_project_schema_session(project_id) as tenant_session:
            tenant_session.query(UserRole).filter(
                UserRole.user_id.in_(user_ids)
            ).delete()
            for role_name in new_roles:
                role = tenant_session.query(Role).filter(Role.name == role_name).first()
                for user_id in user_ids:
                    if role:
                        user_role = UserRole(user_id=user_id, role_id=role.id)
                        tenant_session.add(user_role)
            tenant_session.commit()
            return True

    @web.rpc("admin_get_user_roles", "get_user_roles")
    def get_user_roles(self, project_id: int, user_id: int) -> list[dict]:
        assert project_id is not None, 'project_id cannot be None'
        with db.with_project_schema_session(project_id) as tenant_session:
            user_roles = tenant_session.query(UserRole).with_entities(UserRole.role_id).filter(
                UserRole.user_id == user_id).all()
            user_roles = [role[0] for role in user_roles]
            roles = tenant_session.query(Role).filter(Role.id.in_(user_roles)).all()
            return [RoleDetailModel.from_orm(role).dict() for role in roles]

    @web.rpc('admin_check_user_in_project', 'check_user_in_project')
    def check_user_in_project(self, project_id: int, user_id: Optional[int] = None, **kwargs) -> bool:
        # log.info('Checking if user %s is in project %s', user_id, project_id)
        if not user_id:
            log.info('User is None. Trying to get user from flask.g ...')
            try:
                user_id = int(g.auth.id)
            except (AttributeError, TypeError, ValueError):
                return False
        # log.debug('Checking if user %s is in project %s', user_id, project_id)

        try:
            with db.with_project_schema_session(project_id) as tenant_session:
                user = tenant_session.query(UserRole).filter(UserRole.user_id == user_id).first()
                return bool(user)
        except ProgrammingError:
            # if project schema does not exist
            return False

    @web.rpc('admin_check_user_in_projects', 'check_user_in_projects')
    def check_user_in_projects(self, project_ids: list[int], user_id: Optional[int] = None, **kwargs) -> list[int]:
        if not user_id:
            log.info('User is None. Trying to get user from flask.g ...')
            try:
                user_id = int(g.auth.id)
            except (AttributeError, TypeError, ValueError):
                return []
        #
        expressions = []
        #
        from tools import project_constants as pc
        project_schema_tpl = pc["PROJECT_SCHEMA_TEMPLATE"]
        #
        for project_id in project_ids:
            project_table = table(
                UserRole.__table__.name,
                column(UserRole.user_id.name),
                schema=project_schema_tpl.format(project_id),
            )
            #
            expressions.append(
                select(
                    literal(project_id).label("project_id")
                ).where(
                    project_table.c.user_id == user_id
                )
            )
        #
        def chunked_iterable(iterable, chunk_size=100):
            for i in range(0, len(iterable), chunk_size):
                yield iterable[i:i + chunk_size]

        user_project_ids = set()

        with db.with_project_schema_session(None) as session:
            for chunked_expressions in chunked_iterable(expressions):
                query = union(*chunked_expressions)
                result = session.execute(query).all()
                for row in result:
                    user_project_ids.add(row.project_id)

        user_project_ids = list(user_project_ids)
        user_project_ids.sort()

        return user_project_ids

    @web.rpc('admin_get_project_system_user', 'get_project_system_user')
    def get_project_system_user(self, project_id: int, **kwargs) -> Optional[dict]:
        from tools import auth, project_constants as pc
        try:
            return auth.get_user(email=pc['PROJECT_USER_EMAIL_TEMPLATE'].format(project_id))
        except (NoResultFound, RuntimeError):
            ...
        return

    @web.rpc('admin_get_distinct_user_ids', 'get_distinct_user_ids')
    def get_distinct_user_ids(self, project_id: int, **kwargs) -> List[int]:
        with db.with_project_schema_session(project_id) as tenant_session:
            result = tenant_session.query(UserRole.user_id).distinct().all()
            user_ids = [row[0] for row in result]
            return list(user_ids)
