"""Simple declarative control interface to add to a class as a mixin."""

class Controllable:
    # Dictionary of parameter name to a tuple of parser/validator function.
    # Validators should raise ValueError for invalid content.
    parameters = {}

    def set_parameter(self, name, value):
        """Set the named parameter using setattr if value parses correctly.

        Raise ValueError if the name is invalid or the value does not parse
        successfully.
        """
        try:
            parser = self.parameters[name]
        except KeyError:
            raise ValueError('No parameter with name "{}".'.format(name))

        parsed = parser(value)
        setattr(self, name, parsed)