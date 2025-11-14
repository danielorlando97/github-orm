import requests

from github_orm.tools.github_handler_base import GitHubHandlerBase
from github_orm.tools.github_client import GitHubClient
from github_orm.tools.property_base import PropertyBase

class Branch(GitHubHandlerBase):
    """Branch model with dynamic naming"""
    
    class Name(PropertyBase):
        def _get_data_value(self, handler_data: Dict[str, Any]) -> str:
            return handler_data['branch']
    
    
    
    # objects = None  # Will be set as class attribute
    
    # def __init__(self, context: Optional[ExecutionContext] = None):
    #     super().__init__(context)
    #     self._resolve_name()

    # def _resolve_name(self) -> None:
    #     """Resolves branch name from Name field if context has variables"""
    #     if not self._context.resolved_variables:
    #         return
        
    #     for attr_name in dir(self.__class__):
    #         if attr_name.startswith("_"):
    #             continue
    #         attr = getattr(self.__class__, attr_name)
    #         if isinstance(attr, Name):
    #             if attr.variable_name in self._context.resolved_variables:
    #                 resolved_name = attr.resolve(
    #                     **{attr.variable_name: self._context.resolved_variables[attr.variable_name]}
    #                 )
    #                 setattr(self, attr_name, self._context.resolved_variables[attr.variable_name])
    #                 # Update context with resolved branch name if needed
    #                 if not self._context.branch:
    #                     self._context.branch = resolved_name
    
    # @classmethod
    # def _setup_objects(cls):
    #     """Sets up the objects manager"""
    #     if cls.objects is None:
    #         cls.objects = Manager(cls)