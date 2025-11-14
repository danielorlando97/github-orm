def classproperty(func):
    class ClassPropertyDescriptor:
        def __init__(self, func):
            self.func = func

        def __get__(self, instance, owner):
            return self.func(owner)

    return ClassPropertyDescriptor(func)