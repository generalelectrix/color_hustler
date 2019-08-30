import math
from random import Random
from . import frame_clock
from .controllable import Controllable

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
        return
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

    return [float(i) for i in items]

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

def validate_mode(mode):
    if mode not in (Noise.UNIFORM, Noise.GAUSSIAN):
        raise ValueError("Invalid random mode: {}".format(mode))
    return mode

class Noise(ParameterGenerator):
    parameters = dict(mode=validate_mode, center=float, width=float)

    UNIFORM = 'uniform'
    GAUSSIAN = 'gaussian'
    """Generate random numbers."""
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


class Function(ParameterGenerator):
    """Provide the value of a temporal, periodic function."""
    def __init__(self, rate, func):
        """Create a function generator with a specified function.

        func should take two positional arguments: (phase, rate)

        Internally keeps track of phase on the range [0.0, 1.0)
        """
        self.rate = rate
        self.func = func
        self._phase = 0
        self.last_called = frame_clock.time()

    @property
    def phase(self):
        return self._phase

    @phase.setter
    def phase(self, phase):
        self._phase = phase % 1.0

    def get(self):
        self.phase += (frame_clock.time() - self.last_called)/self.rate.period
        return self.func(self.phase, self.rate)

# --- modulators ---

class Modulator(object):
    """Base class for tools to modulate a parameter stream."""
    def __init__(self, preprocessor=None, postprocessor=None):
        """Register pre- and post-processors for value extraction from complex streams.

        Args:
            preprocessor: a function that takes the input stream and returns the value
                on which to run the modulation operation
            postprocessor: a function that takes the original input stream and the modulated
                value and returns the modulated stream.
        """
        self.preprocessor = preprocessor
        self.postprocessor = postprocessor

    def modulation_operation(self, signal):
        """Apply the modulation operation to the signal.

        Abstract method.
        """
        raise NotImplementedError("Inheriting classes must override this method.")

    def modulate(self, signal):
        """Apply the pre- and post-processors astride the modulation operation."""
        if self.preprocessor:
            value = self.preprocessor(signal)
        else:
            value = signal

        mod_value = self.modulation_operation(value)

        if self.postprocessor:
            mod_value = self.postprocessor(signal, mod_value)

        return mod_value

class StaticModulator(Modulator):
    """Use a fixed value to modulate a signal.

    Some uses of this class are things like adding fixed offsets.
    """
    def __init__(self, value, operation, **kwargs):
        """Create a modifier with a static value and operation.

        Args:
            value: the value to pass to operation
            operation: a function that takes the signal as the first
                argument and the fixed value as the second argument and returns the
                modulated value.
        """
        super(StaticModulator, self).__init__(**kwargs)
        self.value = value
        self.operation = operation

    def modulation_operation(self, signal):
        return self.operation(signal, self.value)

class DynamicModulator(Modulator):
    """Use another parameter generator to modulate a signal."""
    def __init__(self, pgen, operation, **kwargs):
        """Create a modifier with a dynamic value and operation.

        Args:
            pgen: the parameter generator use
            operation: a function that takes a signal value as the first
                argument and the dynamic value as the second argument and returns the
                modulated value.
        """
        super(DynamicModulator, self).__init__(**kwargs)
        self.pgen = pgen
        self.operation = operation

    def modulation_operation(self, signal):
        return self.operation(signal, self.pgen.get())

class BrickwallLimiter(Modulator):
    """Hard-limit a parameter to be within certain bounds."""
    def __init__(self, min_limit=None, max_limit=None, clip_operation=clamp, **kwargs):
        """Create a new brickwall limiter.

        Args:
            min_limit: the minimum value this parameter may take.  If None, no
                minimum limit is imposed.
            max_limit: the maximum value this parameter may take.  If None, no
                maximum limit is imposed.
            clip_operation: a function with the signature
                f(value, min_limit, max_limit) -> modulated value
                default is clamp
        """
        super(BrickwallLimiter, self).__init__(**kwargs)
        self.min_limit = min_limit
        self.max_limit = max_limit
        self.operation = clip_operation

    def modulation_operation(self, signal):
        return self.operation(signal, self.min_limit, self.max_limit)

