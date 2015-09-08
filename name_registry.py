"""Registry for named objects.  Does not support renaming.

Implemented as a singleton."""

from functools import wraps

class NameRegistry(dict):
    __instance = None
    def __new__(cls):
        if NameRegistry.__instance is None:
            NameRegistry.__instance = {}
        return NameRegistry.__instance

def named(object_constructor):
    @wraps(object_constructor)
    def add_name_to_registry(self, *args, **kwargs):
        if 'name' in kwargs:
            NameRegistry()[kwargs['name']] = self
            del kwargs['name']
        object_constructor(self, *args, **kwargs)
    return add_name_to_registry