from pylon.core.tools import web


class Event:
    @web.event(f"user_project_action")
    def user_project_action(self, context, event, payload):
        project_id = payload.get('project_id')
        user_ids = self.context.rpc_manager.call.admin_get_users_ids_in_project(project_id)
        self.context.rpc_manager.call.clear_user_projects_cache(
            user_ids
        )

