from .controllable import Controllable
from itertools import cycle
from . import frame_clock

def validate_iterable(subvalidator):
    def validate(items):
        try:
            iter(items)
        except TypeError:
            raise ValueError("Input must be iterable; got {}".format(items))

        values = [subvalidator(i) for i in items]
        if not values:
            raise ValueError("Must provide at least one value.")
        return values
    return validate

def validate_bank(text):
    parsed = validate_iterable(validate_iterable(int))(text)
    return cycle(parsed)


class GoboHustler(Controllable):
    parameters = dict(
        easing=float,
        bank=validate_bank,
    )

    def __init__(self, param_gen, trig, rotos):
        self.easing = 0.1
        self.param_gen = param_gen
        self.controls = []

        self.trig = trig

        self.rotos = rotos

        for roto in rotos:
            self.controls.extend(roto.get_controls())

        self.control_params = [Easer(0.0) for _ in self.controls]

        self.last_render = frame_clock.time()

        self.bank = cycle([[i] for i in range(len(self.control_params))])

    def render(self, dmx_frame):
        now = frame_clock.time()

        dt = now - self.last_render
        self.last_render = now

        if self.trig.trigger():
            input_value = self.param_gen.get()

            # If triggering, set new targets for the next pattern in the bank.
            pattern = next(self.bank)
            for i in pattern:
                self.control_params[i].target = input_value

        for control, param in zip(self.controls, self.control_params):
            value = param.ease(dt, self.easing)
            control(value)

        for roto in self.rotos:
            roto.render(dmx_frame)

class Easer:
    """Linearly ease current value towards target by at most easing/second."""
    def __init__(self, initial_value):
        self.target = initial_value
        self.current = initial_value

    def ease(self, dt, easing):
        dv = self.target - self.current

        dv_max = dt * easing

        self.current += min(dv, dv_max)
        return self.current
