import math
import time
from random import Random
from rate import Rate

# --- parameter generators ---

class ParameterGenerator(object):
    """Base class for parameter generator objects.

    Any parameter generator which is capable of producing a value on its own
    should inherit from this class.
    """

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

class Constant(ParameterGenerator):
    """Helper class to generate constant values."""
    def __init__(self, center):
        self.center = center

    def get(self):
        return self.center

class UniformRandom(ParameterGenerator):
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

class GaussianRandom(ParameterGenerator):
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

class Diffusor(ParameterGenerator):
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
        self.rand_gen = GaussianRandom(0.0, 0.0, seed)

    def get(self):
        """Get the integrated diffusive shift."""
        now = time.time()
        elapsed = now - self.last_called
        width = math.sqrt(elapsed / (4*self.rate.period))
        self.rand_gen.width = width
        self.last_called = now
        return self.rand_gen.get()

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
        self.last_called = time.time()

    @property
    def phase(self):
        return self._phase

    @phase.setter
    def phase(self, phase):
        self._phase = phase % 1.0

    def get(self):
        self.phase += (time.time() - self.last_called)/self.rate.period
        return self.func(self.phase, self.rate)

# --- modulators ---

class Modulator(object):
    """Base class for tools to modulate a parameter stream."""
    def __init__(self):
        raise NotImplementedError("Inheriting classes must define their own "
                                  "constructor.")
    def modulate(self, value):
        """Apply the modulation operation."""
        raise NotImplementedError("Inheriting classes must override this method.")

class StaticModifier(Modulator):
    """Use a fixed value to modulate a signal.

    Some uses of this class are things like adding fixed offsets.
    """
    def __init__(self, value, operation):
        """Create a modifier with a static value and operation.

        Args:
            value: the value to pass to operation
            operation: a function that takes the fixed value as the first
                argument and a signal value as the second argument and returns the
                modulated value.
        """
        self.value = value
        self.operation = operation

    def modulate(self, signal):
        return self.operation(self.value, signal)

# --- parameter generator mutators ---

class Mutator(object):
    """Base class for tools to mutate parameter generators when they are called."""
    def __init__(self):
        raise NotImplementedError("Inheriting classes must define their own "
                                  "constructor.")
    def mutate(self, param_gen):
        """Apply the mutation operation to a specified parameter generator."""
        raise NotImplementedError("Inheriting classes must override this method.")

class Twiddler(Mutator):
    """Generic parameter twiddler."""
    def __init__(self, twiddle_gen, operation):
        """Wrap a creator with a parameter generator and pre-get operation.

        Args:
            param_gen: a parameter generator creating the twiddle value
            operation: a function that takes a param gen as the first argument
                and the twiddle value as the second argument.  this operation
                is what applies the twiddle to the param gen.
        """
        self.twiddle_gen = twiddle_gen
        self.operation = operation

    def mutate(self, param_gen):
        self.operation(param_gen, self.twiddle_gen.get())

# --- chains ---

class FXChain(ParameterGenerator):
    """Base class for linear effects chains."""
    def __init__(self, head):
        """Initialize a linear effects chain with a source."""
        if not hasattr(head, 'get'):
            raise ModulationChainError("The head of an effects chain must have "
                                       "a get method.")
        self.chain = []
        self.source = head

    def append(self, effect):
        """Add an effect to the chain."""
        self.chain.append(effect)

    def pop(self, index=None):
        """Remove and return an effect from the chain."""
        try:
            if index is not None:
                mod = self.chain.pop(index)
            else:
                mod = self.chain.pop()
        except IndexError:
            return None
        return mod

    def insert(self, index, effect):
        """Insert a effect at the specified index, shifting to the right.

        If index is larger than the current chain length, append.
        """
        self.chain.insert(index, effect)

class MutatorZombieHerd(FXChain):
    """Encapsulate a linear chain of Mutators."""

    def get(self):
        """Drive the zombie mutators to action."""
        for zombie in self.chain:
            zombie.mutate(self.source)
        return self.source.get()

class ModulationChain(FXChain):
    """Encapsulate a linear chain of parameter manipulation."""

    def get(self):
        """Render the whole modulation chain."""
        val = self.source.get()
        for mod in self.chain:
            val = mod.modulate(val)
        return val

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

# --- error handling ---

class PGError(Exception):
    pass

class ModulationChainError(PGError):
    pass