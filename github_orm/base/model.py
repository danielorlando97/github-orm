class GitHubModel:

    def __init__(self, **kwargs) -> None:
        _meta = kwargs.pop('meta', None)
        for property, annotation in inspect.get_annotations(self.__class__).items():
            if issubclass(annotation, GitHubFile):
                setattr(self, property, annotation(Meta(**_meta)))
            
            if property in kwargs:
                property_value = kwargs[property]
            else:
                try:
                    property_value = getattr(self, property)
                except AttributeError:
                    raise GitHubOrmError(f"Property {property} not found in {self.__class__.__name__}")
            
            try:
                property_value = annotation(property_value)
            except Exception:
                pass
            
            setattr(self, property, property_value)

    @classproperty
    def objects(cls) -> 'GitHubHandlerManager':
        meta = None
        if hasattr(cls, 'Meta'):
            meta = Meta.from_class(cls.Meta)
        
        files = {}
        # for attr_name in dir(cls):
        #     if attr_name.startswith('_'):
        #         continue
            
        #     if attr_name in ['Meta', 'objects']:
        #         continue
            
        #     attr = getattr(cls, attr_name)
        #     if isinstance(attr, GitHubFile):
        #         cls._properties[attr_name] = attr.objects
        
        return GitHubQueryBuilder(cls, meta, files)