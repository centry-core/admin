from sqlalchemy import Column, Integer, String, UniqueConstraint

from tools import db_tools, db


class Role(db_tools.AbstractBaseMixin, db.Base):
    __tablename__ = "role"
    __table_args__ = (
        UniqueConstraint("name"),
        {"schema": "tenant"}
    )

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(64), nullable=False)


class RolePermission(db_tools.AbstractBaseMixin, db.Base):
    __tablename__ = f"role_permission"
    __table_args__ = (
        UniqueConstraint("role_id", "permission"),
        {"schema": "tenant"}
    )

    id = Column(Integer, primary_key=True)
    role_id = Column(Integer, nullable=False)
    permission = Column(String(64))


class UserRole(db_tools.AbstractBaseMixin, db.Base):
    __tablename__ = "user_role"
    __table_args__ = (
        UniqueConstraint("user_id", "role_id"),
        {"schema": "tenant"}
    )

    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, nullable=False)
    role_id = Column(Integer, nullable=False)
