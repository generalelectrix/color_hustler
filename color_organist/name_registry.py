"""Registry for named objects.  Does not support renaming.

Implemented as a singleton."""

from functools import wraps

class NameRegistry(dict):
    """Global name dictionary.  Implmented as a singleton.

    Using a singleton here simplifies loading saved shows, as there is no explicit
    need to instruct any objects to update their reference to the name registry.
    """
    __instance = None
    def __new__(cls):
        if NameRegistry.__instance is None:
            NameRegistry.__instance = {}
        return NameRegistry.__instance

def register_name(object_constructor):
    """Decorator to add the global name registry to any function.

    Used with constructors to register new objects.
    """
    @wraps(object_constructor)
    def add_name_to_registry(self, *args, **kwargs):
        if 'name' in kwargs:
            NameRegistry()[kwargs['name']] = self
            del kwargs['name']
        object_constructor(self, *args, **kwargs)
    return add_name_to_registry

def get(name):
    """Get a named entity from the registry.

    Just a convenient shorthand for NameRegistry()[name]
    """
    return NameRegistry()[name]

