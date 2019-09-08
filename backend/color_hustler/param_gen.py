import math
from random import Random
from . import frame_clock
from .controllable import Controllable, validate_string_constant
from .rate import RateProperties, Rate

# --- numeric helper functions ---

def in_range(value, min_val=None, max_val=None):
    """Determine if a value is in the interval [min_val, max_val], inclusive.

    Returns the integer 0 if the value is in range, +1 if it is above the max,
    and -1 if it is below the min.
    """
    in_range = 0
    if min_val is not None and value < min_val:
        in_range = -1
    elif max_val is not None and value > max_val:
        in_range = 1
    return in_range

def clamp(value, min_val=None, max_val=None):
    val_in_range = in_range(value, min_val, max_val)
    if val_in_range == 0:
        return value
    elif val_in_range == 1:
        return max_val
    elif val_in_range == -1:
        return min_val

def exclude(value, start, stop):
    """Exclude a value from the range (start, stop).

    Rounds up or down to the closest limit of the range.
    """
    if value > start and value < stop:
        # value is in the excluded range
        # scale the value to a unit float on the given range
        scaled = (value - start) / (stop - start)
        # round the value; if it is 0, it is closer to the start of the range
        if round(scaled) < 0.5:
            return start
        else:
            return stop
    else:
        return stop


def fold(value, min_val=None, max_val=None):
    """Fold a floating-point value back into a given range."""
    while True:
        val_in_range = in_range(value, min_val, max_val)
        if val_in_range == 0:
            break
        elif val_in_range == 1:
            value = 2*max_val - value
        elif val_in_range == -1:
            value = 2*min_val - value
    return value

def wrap(value, min_val, max_val):
    return ((value - min_val) % max_val) + min_val

def scale(value, min_val, max_val):
    """Scale a unit float to a specified range."""
    return (value * (max_val - min_val)) + min_val

_constrainers = {
    'fold': fold,
    'clip': clamp,
    'wrap': wrap,
}

# --- parameter generators ---

class ParameterGenerator(Controllable):
    """Base class for parameter generator objects.

    Any parameter generator which is capable of producing a value on its own
    should inherit from this class.
    """
    def get(self):
        """"Get the next raw value from this generator.

        Inheriting classes should override this method.
        """
        raise NotImplementedError("Inheriting classes must override this method.")

    def get_constrained(self, min_val, max_val, mode='fold'):
        """Get the next value from this generator wrapped to a given interval.

        The behavior of this method differs depending on the value of the fold
        argument.  If fold=True (default), out-of-range values will be iteratively
        folded back into range.  Otherwise, out-of-range values will be clipped.
        """
        val = self.get()
        return _constrainers[mode](val, min_val, max_val)

class Constant(ParameterGenerator):
    """Helper class to generate constant values."""
    parameters = dict(center=float)

    def __init__(self, center):
        self.center = center

    def get(self):
        return self.center

def validate_constant_list(items):
    try:
        iter(items)
    except TypeError:
        raise ValueError("Input to ConstantList must be iterable; got {}".format(items))

    values = [float(i) for i in items]
    if not values:
        raise ValueError("Must provide at least one value.")
    return values

class ConstantList(ParameterGenerator):
    """Choose from a list of constant values."""
    parameters = dict(values=validate_constant_list, random=bool)

    def __init__(self, values, random=False, seed=None):
        self.values = values
        self.random = random
        self.index = 0
        self.rand_gen = Random()
        if seed is not None:
            self.rand_gen.seed(seed)

    def get(self):
        if self.random:
            index = self.rand_gen.randint(0, len(self.values)-1)
            return self.values[index]

        self.index = (self.index + 1) % len(self.values)
        return self.values[self.index]


class Noise(ParameterGenerator):
    """Generate random numbers."""
    UNIFORM = 'uniform'
    GAUSSIAN = 'gaussian'

    parameters = dict(
        mode=validate_string_constant([UNIFORM, GAUSSIAN], "noise mode"),
        center=float,
        width=float)
    def __init__(self, mode, center, width, seed=None):
        """
        Args:
            mode: NoiseMode
            center: the centroid of the generated number cloud
            width: the half-width or standard deviation of the generated number cloud
            seed (optional): specify the seed for this random number generator.
        """
        self.mode = mode
        self.center = center
        self.width = width
        self._gen = Random()
        if seed is not None:
            self._gen.seed(seed)

    def get(self):
        if self.mode == self.GAUSSIAN:
            return self._gen.gauss(self.center, self.width)
        if self.mode == self.UNIFORM:
            return self._gen.uniform(
                self.center - self.width, self.center + self.width)
        raise ValueError("Unknown noise mode: {}".format(self.mode))

PI = math.pi
HALF_PI = math.pi / 2.0
TWOPI = 2*math.pi

def sine(angle, smoothing, duty_cycle, pulse):
    angle = angle % 1.0

    if angle > duty_cycle or duty_cycle == 0.0:
        return 0.0

    angle = angle / duty_cycle
    if pulse:
        return (math.sin(TWOPI * angle - HALF_PI) + 1.0) / 2.0

    return math.sin(TWOPI * angle)

def triangle (angle, smoothing, duty_cycle, pulse):
    """Generate a point on a unit triangle wave from angle."""
    angle = angle % 1.0

    if angle > duty_cycle or duty_cycle == 0.0:
        return 0.0

    angle = angle / duty_cycle
    if pulse:
        if angle < 0.5:
            return 2.0 * angle
        return 2.0 * (1.0 - angle)

    if angle < 0.25:
        return 4.0 * angle
    elif angle > 0.75:
        return 4.0 * (angle - 1.0)
    else:
        return 2.0 - 4.0 * angle

def square(angle, smoothing, duty_cycle, pulse):
    """Generate a point on a square wave from angle and smoothing."""

    angle = angle % 1.0

    if angle > duty_cycle or duty_cycle == 0.0:
        return 0.0

    angle = angle / duty_cycle
    if pulse:
        return square(angle/2.0, smoothing, 1.0, False)


    if smoothing == 0.0:
        if angle < 0.5:
            return 1.0
        return -1.0

    if angle < smoothing:
        return angle / smoothing
    elif angle > (0.5 - smoothing) and angle < (0.5 + smoothing):
        return -(angle - 0.5)/smoothing
    elif angle > (1.0 - smoothing):
        return (angle - 1.0)/smoothing
    elif angle >= smoothing and angle <= 0.5 - smoothing:
        return 1.0
    else:
        return -1.0

def sawtooth(angle, smoothing, duty_cycle, pulse):
    """Generate a point on a sawtooth wave from angle and smoothing."""

    angle = angle % 1.0

    if angle > duty_cycle or duty_cycle == 0.0:
        return 0.0

    angle = angle / duty_cycle
    if pulse:
        return sawtooth(angle/2.0, smoothing, 1.0, False)

    if smoothing == 0.0:
        if angle < 0.5:
            return 2.0 * angle
        return 2.0 * (angle - 1.0)

    if angle < 0.5 - smoothing:
        return angle / (0.5 - smoothing)
    elif angle > 0.5 + smoothing:
        return (angle - 1.0) / (0.5 - smoothing)
    else:
        return -(angle - 0.5)/smoothing

def float_unit(value):
    return clamp(float(value), 0.0, 1.0)

# TODO: extract the function generator from pytunnel
class Waveform(ParameterGenerator, RateProperties):
    """Provide the value of a temporal, periodic function."""
    SINE = "sine"
    SQUARE = "square"
    SAWTOOTH = "sawtooth"
    TRIANGLE = "triangle"

    _funcs = {
        SINE: sine,
        SQUARE: square,
        SAWTOOTH: sawtooth,
        TRIANGLE: triangle,
    }

    parameters = dict(
        waveform=validate_string_constant([SINE, SAWTOOTH, TRIANGLE, SQUARE], "waveform"),
        period=float,
        hz=float,
        bpm=float,
        reset=bool,
        smoothing=float_unit,
        duty_cycle=float_unit,
        pulse=bool,
        amplitude=float,
    )

    def __init__(self, rate=None, waveform=SINE):
        """Create a function generator with a specified function.

        Internally keeps track of phase on the range [0.0, 1.0)
        """
        self.pulse = False
        self.smoothing = 0.0
        self.duty_cycle = 1.0
        self.amplitude = 0.0

        if rate is None:
            rate = Rate(hz=1.0)

        self._rate = rate
        self.waveform = waveform
        self._phase = 0.0
        self._last_update = frame_clock.time()

    @property
    def reset(self):
        return None

    @reset.setter
    def reset(self, _):
        self._phase = 0.0

    def _update_phase(self, now):
        delta_t = now - self._last_update
        self._phase = (self._phase + (delta_t * self.hz)) % 1.0
        self._last_update = now

    def get(self):
        now = frame_clock.time()
        if now != self._last_update:
            self._update_phase(now)

        func = self._funcs[self.waveform]
        val = func(self._phase, self.smoothing, self.duty_cycle, self.pulse)
        return self.amplitude * val

# --- modulators ---

class Modulator(ParameterGenerator):
    """Modulate a parameter stream using another."""
    ADD = 'add'
    SUBTRACT = 'subtract'
    MULTIPLY = 'multiply'

    parameters = dict(
        operation=validate_string_constant([ADD, SUBTRACT, MULTIPLY], "modulation mode"))

    def __init__(self, source, modulation_gen, operation=ADD):
        self.source = source
        self.modulation_gen = modulation_gen
        self.operation = operation

    def get(self):
        input_val = self.source.get()
        mod_val = self.modulation_gen.get()

        if self.operation == self.ADD:
            return input_val + mod_val
        if self.operation == self.SUBTRACT:
            return input_val - mod_val
        if self.operation == self.MULTIPLY:
            return input_val * mod_val

        raise ValueError("Unknown modulation operation: {}".format(self.operation))


class BrickwallLimiter(ParameterGenerator):
    """Hard-limit a parameter to be within certain bounds."""
    parameters = dict(
        operation=validate_string_constant(_constrainers.keys(), "limiter mode"))

    def __init__(self, source, min_limit=None, max_limit=None, clip_operation='clip'):
        """Create a new brickwall limiter.

        Args:
            min_limit: the minimum value this parameter may take.  If None, no
                minimum limit is imposed.
            max_limit: the maximum value this parameter may take.  If None, no
                maximum limit is imposed.
            clip_operation: 'fold', 'clip', or 'wrap'
        """
        self.source = source
        self.min_limit = min_limit
        self.max_limit = max_limit
        self.operation = clip_operation

    def get(self):
        return _constrainers[self.operation](
            self.source.get(), self.min_limit, self.max_limit)
