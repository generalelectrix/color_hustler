import math
import time
from random import Random
from rate import Rate

class ParameterGenerator(object):
    """Helper class to generate random numbers with useful properties."""

    def __init__(self):
        """Inheriting classes should define their own constructor."""
        raise NotImplementedError("Inheriting classes must define their own constructor.")

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
        if mode == 'fold':
            return fold(val, min_val, max_val)
        elif mode == 'clip':
            return clamp(val, min_val, max_val)
        elif mode == 'wrap':
            return wrap(val, min_val, max_val)
        else:
            raise PGError("Unrecognized constraint mode: {}".format(mode))

class ConstantPG(ParameterGenerator):
    """Helper class to generate constant values."""
    def __init__(self, center):
        self.center = center

    def get(self):
        return self.center

class UniformRandomPG(ParameterGenerator):
    """Generate unformly-distributed random numbers."""
    def __init__(self, center, width, seed=None):
        """Create a new uniform random number generator.

        Will generate random numbers on the interval [center-width, center+width).

        Args:
            center: the centroid of the generated number cloud
            width: the half-width of the generated number cloud
            seed (optional): specify the seed for this random number generator.
        """
        self.center = center
        self.width = width
        self.gen = Random()
        if seed is not None:
            self.gen.seed(seed)

    def get(self):
        """Generate the next random value."""
        return self.gen.uniform(self.min_val, self.max_val)

    @property
    def min_val(self):
        return self.center - self.width

    @property
    def max_val(self):
        return self.center + self.width

class GaussianRandomPG(ParameterGenerator):
    """Generate gaussian-distributed random numbers."""
    def __init__(self, center, width, seed=None):
        """Create a new gaussian random number generator.

        Will generate random numbers about center with standard deviation width.

        Args:
            center: the centroid of the generated number cloud
            width: the standard deviation of the generated number cloud
            seed (optional): specify the seed for this random number generator.
        """
        self.center = center
        self.width = width
        self.gen = Random()
        if seed is not None:
            self.gen.seed(seed)

    def get(self):
        """Generate the next random value."""
        return self.gen.gauss(self.center, self.width)

class Diffusor(object):
    """Generate diffusive motion in a random walk style.

    When polled for a value, a diffusor returns a random value selected from
    a gaussian distribution centered about zero whose standard deviation increases
    with sqrt(time), mimicking a random walk in the continuous limit.

    After one period given by rate, the full-width half-max of this distribution
    is defined to be 1.0, implying what amounts to a completely random shift.
    """
    def __init__(self, rate, seed=None):
        """Initialize a diffusor with a rate."""
        self.rate = rate
        self.last_called = time.time()
        self.rand_gen = GaussianRandomPG(0.0, 0.0, seed)

    def get(self):
        """Get the integrated diffusive shift."""
        now = time.time()
        elapsed = now - self.last_called
        width = math.sqrt(elapsed / (4*self.rate.period))
        self.rand_gen.width = width
        self.last_called = now
        return self.rand_gen.get()

class Twiddle(object):
    """Wrapper around a creator object to twiddle a parameter when get is called."""
    def __init__(self, creator, param_gen, operation):
        """Wrap a creator with a parameter generator and pre-get operation.

        Args:
            creator: any object with a get method
            param_gen: a parameter generator to twiddle the creator
            operation: a function that takes the creator as the first argument
                and the param_gen's output as the second argument.  this operation
                is what applies the twiddle to the creator.
        """
        self.creator = creator
        self.param_gen = param_gen
        self.operation = operation

    def get(self):
        self.operation(self.creator, self.param_gen.get())
        return self.creator.get()


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

class PGError(Exception):
    pass