from pydantic import ValidationError

from tools import rpc_tools

from pylon.core.tools import web


class RPC:
    @web.rpc("get_roles", "admin_get_roles")
    @rpc_tools.wrap_exceptions(ValidationError)
    def get_roles(self, **kwargs) -> list[str]:
        roles = ["admin", "editor", "viewer", "role1"]
        return roles
