import inspect
from github_orm.tools.utils import classproperty
from github_orm.github_client.router import GitHubRouter
from github_orm.github_client.query_builder import GitHubQueryBuilder
from github_orm.tools.errors import GitHubOrmError
from github_orm.base.file_property import GitHubFileProperty


class GitHubModel:

    def __init__(self, **kwargs) -> None:
        _meta = kwargs.pop('meta', None)
        for property, annotation in inspect.get_annotations(self.__class__).items():
            if issubclass(annotation, GitHubFileProperty):
                setattr(self, property, annotation(GitHubRouter(**_meta)))
            
            if property in kwargs:
                property_value = kwargs[property]
            else:
                try:
                    property_value = getattr(self, property)
                except AttributeError:
                    raise GitHubOrmError(
                        f"Property {property} not found in "
                        f"{self.__class__.__name__}"
                    )
            
            try:
                property_value = annotation(property_value)
            except Exception:
                pass
            
            setattr(self, property, property_value)

    @classproperty
    def objects(cls) -> 'GitHubQueryBuilder':
        meta = None
        if hasattr(cls, 'Meta'):
            meta = GitHubRouter.from_class(cls.Meta)
        
        files = {}
        # for attr_name in dir(cls):
        #     if attr_name.startswith('_'):
        #         continue
            
        #     if attr_name in ['Meta', 'objects']:
        #         continue
            
        #     attr = getattr(cls, attr_name)
        #     if isinstance(attr, GitHubFileProperty):
        #         cls._properties[attr_name] = attr.objects
        
        return GitHubQueryBuilder(cls, meta, files)