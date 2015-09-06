"""A player piano for the color organ.

Necessary elements:

Conversion of a color into a midi event in color organ scheme.

Velocity = intensity
Hue = midi note
Use 0 to 127 for maximum expression (still not a lot of colors...)

Saturation: set as a control change before sending the note
"""

import logging
import multiprocessing
import traceback
import time
from Queue import Empty
from multiprocessing import Queue, Process
from random import Random

import mido

# control mappings
CC_SAT = 11

# color organ style HSB color

class Color(object):
    """Roll my own HSB color to match how the color organ works."""
    def __init__(self, hue, saturation, brightness):
        """HSB on unit float intervals."""
        self.hue = hue
        self.saturation = saturation
        self.brightness = brightness

    def __str__(self):
        return "Color; (h,s,b) = ({},{},{})".format(self.hue, self.saturation, self.brightness)

    def __eq__(self, other):
        if isinstance(other, Color):
            return (self.h == other.h and
                    self.s == other.s and
                    self.b == other.b)

    def __ne__(self, other):
        return not self == other

    @property
    def h(self):
        return self.hue
    @property
    def s(self):
        return self.saturation
    @property
    def b(self):
        return self.brightness

# possibly useful color constants

def red():
    return Color(0.5, 1.0, 1.0)

def green():
    return Color(1.0/6.0, 1.0, 1.0)

def blue():
    return Color(5.0/6.0, 1.0, 1.0)

def cyan():
    return Color(0.0, 1.0, 1.0)

def yellow():
    return Color(1.0/3.0, 1.0, 1.0)

def magenta():
    return Color(2.0/3.0, 1.0, 1.0)

def black():
    return Color(0.0, 0.0, 0.0)

def white():
    return Color(0.0, 0.0, 1.0)

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

    def get_constrained(self, min_val=None, max_val=None, fold_val=True):
        """Get the next value from this generator wrapped to a given interval.

        The behavior of this method differs depending on the value of the fold
        argument.  If fold=True (default), out-of-range values will be iteratively
        folded back into range.  Otherwise, out-of-range values will be clipped.
        """
        val = self.get()
        if fold_val:
            return fold(val, min_val, max_val)
        else:
            return clamp(val, min_val, max_val)

class ConstantPG(ParameterGenerator):
    """Helper class to generate constant values."""
    def __init__(self, value):
        self.value = value

    def get(self):
        return self.value

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
    def __init__(self, center, sigma, seed=None):
        """Create a new gaussian random number generator.

        Will generate random numbers about center with standard deviation sigma.

        Args:
            center: the centroid of the generated number cloud
            sigma: the standard deviation of the generated number cloud
            seed (optional): specify the seed for this random number generator.
        """
        self.center = center
        self.sigma = sigma
        self.gen = Random()
        if seed is not None:
            self.gen.seed(seed)

    def get(self):
        """Generate the next random value."""
        return self.gen.gauss(center, sigma)


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

def scale(value, min_val, max_val):
    """Scale a unit float to a specified range."""
    return (value * (max_val - min_val)) + min_val

class HSBColorGenerator(object):
    """Random color generation."""

    def __init__(self, h_gen, s_gen, b_gen):
        """Create a new random color generator."""
        self.h_gen = h_gen
        self.s_gen = s_gen
        self.b_gen = b_gen

    def get(self):
        """Get the next random color from this generator."""
        h_val = self.h_gen.get_constrained(0.0, 1.0)
        s_val = self.s_gen.get_constrained(0.0, 1.0)
        b_val = self.b_gen.get_constrained(0.0, 1.0)
        return Color(h_val, s_val, b_val)

# conversion from unit float to stupid midi 7-bit number

def unit_float_to_7bit(number):
    """Convert a float on the range [0,1] to an int on the range [0,127]."""
    return min(int(number*128), 127)

def note_onoff_pair(channel, note, velocity):
    on = mido.Message('note_on', channel=channel, note=note, velocity=velocity)
    off = mido.Message('note_off', channel=channel, note=note, velocity=velocity)

    return on, off

class Rate(object):
    """Helper class for working with rates."""
    def __init__(self, bpm=None, hz=None, period=None):
        """Create a new rate.

        Must supply exactly one named optional argument {bpm, hz, period}.
        """
        self.hz = None

        if bpm is not None:
            self.bpm = bpm
        elif hz is not None:
            self.hz = hz
        elif period is not None:
            self.period = period
        else:
            raise RateError("Must supply at least one argument to Rate().")

    @property
    def bpm(self):
        return self.hz * 60.0

    @bpm.setter
    def bpm(self, bpm):
        self.hz = bpm / 60.0

    @property
    def period(self):
        return 1.0 / self.hz

    @period.setter
    def period(self, period):
        self.hz = 1.0 / period

class ClockTrigger(object):
    """Polling-based scheduling of an operation."""
    def __init__(self, rate):
        """Create a new ClockTrigger.

        This trigger will initially be in a state where it will fire immediately
        when first polled.
        """
        self.rate = rate
        self.last_trig = time.time() - self.period

    @property
    def period(self):
        return self.rate.period

    def reset(self):
        """Reset the trigger timer to now."""
        self.last_trig = time.time()

    def trigger(self):
        """Return True if it is time to trigger and reset trigger clock."""
        if self.overdue():
            self.reset()
            return True
        else:
            return False

    def overdue(self):
        """Return True is at least one period has passed since the last trigger."""
        return True if self.time_until_trig() <= 0.0 else False

    def time_until_trig(self):
        """Return the time until the next trigger event.

        If this trigger hasn't fired but is overdue, return a negative time.
        """
        return self.period - (time.time() - self.last_trig)

    def block_until_trig(self):
        """Block thread execution until the next trigger event."""
        while True:
            time_until_trig = self.time_until_trig()
            if time_until_trig <= 0.0:
                # time to trigger
                break
            else:
                # wait 95% of the remaining time and run again
                time.sleep(0.95*time_until_trig)

class ColorOrgan(object):
    """Takes a stream of colors and sends them to a LD50 color organ.

    Also knows how to select banks.  Notes are always sent as a on/off pair
    with no sustain period, as that would be more than I want to deal with
    this late at night and this close to the show :)
    """

    def __init__(self, port, ctrl_channel, bank_channel, banks=None):
        self.port = port
        self.ctrl_channel = ctrl_channel
        self.bank_channel = bank_channel
        if banks is None:
            self.banks = {}
        else:
            self.banks = banks

    def send_color(self, color):
        """Send a color message to the color organ."""
        note = unit_float_to_7bit(color.h)
        velocity = unit_float_to_7bit(color.b)
        saturation = unit_float_to_7bit(color.s)

        sat_msg = mido.Message('control_change',
                               channel=self.ctrl_channel,
                               control=CC_SAT,
                               value=saturation)
        on_msg, off_msg = note_onoff_pair(channel=self.ctrl_channel, note=note, velocity=velocity)

        self.port.send(sat_msg)
        self.port.send(on_msg)
        self.port.send(off_msg)

    def select_bank(self, bank):
        """Select a named bank."""
        try:
            bank_note = self.banks[bank]
        except KeyError:
            raise InvalidBankError("{} is not a valid bank.  Valid banks are {}"
                                   .format(bank, self.banks.keys()))
        on, off = note_onoff_pair(channel=self.bank_channel,
                                  note=bank_note,
                                  velocity=127)
        self.port.send(on)
        self.port.send(off)

class ColorOrganistPuppeteer(object):
    """Controller-side interface to a ColorOrganist.

    This class encapsulates starting, commanding, and stopping a ColorOrganist.
    """
    def __init__(self, organist):
        self.organist = organist
        self.organist_process = None
        self.ctrl_queue = None

    def start(self):
        """Start this organist."""
        self.ctrl_queue = Queue()
        self.organist_process = Process(target=self.organist.play,
                                        args=(self.ctrl_queue,))
        self.organist_process.start()

    def stop(self):
        """Stop this organist."""
        self.ctrl_queue.put(ColorOrganistCommand('stop'))
        self.organist_process.join()

class ColorOrganistCommand(object):
    """Class encapsulating a command to a ColorOrganist.

    name must be a valid ColorOrganist method."""
    def __init__(self, name, *args, **kwargs):
        self.name = name
        self.args = args
        self.kwargs = kwargs

class ColorOrganist(object):
    """Class encapsulating a process which runs an independent color organ.

    Uses a queue to receive command messages; this command queue is continuously
    drained in the intervals between when this organist is triggered to send a
    note.
    """

    def __init__(self, organ, color_gen, note_trig):
        self.organ = organ
        self.color_gen = color_gen
        self.note_trig = note_trig
        self.quit = False

    def process_command(self, command):
        """Process a command from the command queue."""
        # try to get the
        try:
            command_call = getattr(self, command.name)
        except AttributeError:
            logging.error("Organist received an unknown command key: {}".format(command_key))
            return
        try:
            command_call(*command.args, **command.kwargs)
        except Exception:
            logging.error("An error occurred during organist command execution:")
            logging.error(traceback.format_exc())

    # --- organist command methods ---

    def stop(self):
        self.quit = True

    def replace_color_gen(self, gen):
        self.color_gen = gen

    def replace_note_trig(self, trig):
        self.note_trig = trig

    def set_trig_rate(self, rate):
        self.note_trig.rate = rate

    def select_bank(self, bank):
        try:
            self.organ.select_bank(bank)
        except InvalidBankError as err:
            logging.error(err)

    # --- main execution method ---

    def play(self, ctrl_queue):
        """Start this organist playing."""
        while True:
            # check if we are done with this organist
            if self.quit:
                return

            # if we are ready to trigger, get a color and send a note
            if self.note_trig.trigger():
                col = self.color_gen.get()
                print "sending color {}".format(col)
                self.organ.send_color(col)

            # otherwise, find out how much time we have to process control events
            # block the thread waiting for a control event for 95% of that time
            # to ensure we aren't late on the next trigger.
            else:
                time_until_trig = self.note_trig.time_until_trig()
                try:
                    command_action = ctrl_queue.get(block=True, timeout=0.95*time_until_trig)
                except Empty:
                    # if no control event happened, do nothing
                    command_action = None

                # if we received a control event, process it
                if command_action is not None:
                    self.process_command(command_action)




def test_color_organist_functions_local():

    p = mido.open_output()

    co = ColorOrgan(p, 0, 1, {'linear': 0, 'all': 1})

    co.select_bank('linear')

    for _ in xrange(8):
        co.send_color(red())
        time.sleep(0.3)

    co.select_bank('all')
    co.send_color(cyan())
    time.sleep(1.0)
    co.send_color(magenta())
    time.sleep(1.0)
    co.send_color(white())

    # check random color generation
    # full brightness, unform random hue and sat
    h_gen = UniformRandomPG(0.5, 0.5)
    s_gen = UniformRandomPG(0.5, 0.5)
    b_gen = ConstantPG(1.0)

    c_gen = HSBColorGenerator(h_gen, s_gen, b_gen)

    co.select_bank('linear')

    for _ in xrange(24):
        col = c_gen.get()
        co.send_color(col)
        time.sleep(0.3)

def test_co_functions_process():
    p = mido.open_output()

    organ = ColorOrgan(p, 0, 1, {'linear': 0, 'all': 1})

    h_gen = UniformRandomPG(0.5, 0.5)
    s_gen = UniformRandomPG(0.5, 0.5)
    b_gen = ConstantPG(1.0)

    c_gen = HSBColorGenerator(h_gen, s_gen, b_gen)

    note_trig = ClockTrigger(Rate(bpm=120.))

    organist = ColorOrganist(organ, c_gen, note_trig)

    org_ctrl = ColorOrganistPuppeteer(organist)

    org_ctrl.start()
    time.sleep(4.0)
    org_ctrl.stop()

class InvalidBankError(Exception):
    pass

class RateError(Exception):
    pass



if __name__ == '__main__':
    #test_color_organist_functions_local()
    test_co_functions_process()


































