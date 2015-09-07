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
from threading import Thread
from Queue import Empty
import multiprocessing as mp
from multiprocessing import Process

from contextlib import contextmanager

import mido

import param_gen as pgen
from color import Color, HSBColorGenerator
from color import red, green, blue, cyan, magenta, yellow
from rate import Rate, ClockTrigger

# control mappings
CC_SAT = 11

# conversion from unit float to stupid midi 7-bit number

def unit_float_to_7bit(number):
    """Convert a float on the range [0,1] to an int on the range [0,127]."""
    return min(int(number*128), 127)

def note_onoff_pair(channel, note, velocity):
    on = mido.Message('note_on', channel=channel, note=note, velocity=velocity)
    off = mido.Message('note_off', channel=channel, note=note, velocity=velocity)

    return on, off


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
        self.ctrl_queue = mp.Queue()
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

class MidiService(object):
    """The interface to a process which handles interfacing with a midi port."""

    def __init__(self, port_name):
        """Create a new MidiHandler encapsulating a midi port."""
        self.port_name = port_name
        self.running = False
        self.ctrl_queue = mp.Queue()

    def start(self):
        """Start the midi handling service."""
        if self.running:
            return
        # midi handling service function
        def run_midi_service(port_name, ctrl_queue):
            # open the midi port
            try:
                print mido.get_output_names()
                port = mido.open_output(port_name)
                print port
            except Exception:
                logging.error("Could not open midi port {}:".format(port_name))
                logging.error(traceback.format_exc())
                return

            # run the midi service
            while True:
                # get the next message from the queue
                msg_type, msg = ctrl_queue.get()
                # process a command message
                if msg_type == 'command':
                    if msg == 'stop':
                        return
                # process a midi event
                elif msg_type == 'midi':
                    port.send(msg)

        self.midi_process = Thread(target=run_midi_service,
                                    args=(self.port_name, self.ctrl_queue))
        self.midi_process.start()
        self.running = True

    def stop(self):
        """Stop the midi handling service."""
        if self.running:
            self.ctrl_queue.put(('command', 'stop'))
            self.midi_process.join()
            while not self.ctrl_queue.empty():
                try:
                    self.ctrl_queue.get(False)
                except Empty:
                    pass
            self.ctrl_queue = None
            self.running = False

    def get_client(self):
        """Return a MidiClient connected to this service."""
        return MidiClient(self.ctrl_queue)

    @contextmanager
    def run(self):
        """Run the midi service as a context manager."""
        self.start()
        yield
        self.stop()

class MidiClient(object):
    """Client-side interface to the midi service."""
    def __init__(self, msg_queue):
        self.msg_queue = msg_queue

    def send(self, msg):
        """Send a midi message using this service."""
        self.msg_queue.put(('midi', msg))

def nice_color_gen_default(start_color):
    """Instance an aesthetically pleasing color generator.

    start_color is an optional color to start the generator with.  At the moment,
    this just sets the initial center of the hue generator.

    Hue is driven by a gaussian with width of 0.1.
    Saturation is driven by a gaussian centered at 1.0 with width 0.2.
    Brightness is driven by a gaussian centered at 1.0 with width 0.2.
    """
    h_gen = pgen.GaussianRandomPG(start_color.hue, 0.1)
    s_gen = pgen.GaussianRandomPG(1.0, 0.2)
    b_gen = pgen.GaussianRandomPG(1.0, 0.2)
    return HSBColorGenerator(h_gen, s_gen, b_gen)

def test_hue_gen(start_color):
    """Return a color generator that produces a constant color."""
    h_gen = pgen.ConstantPG(start_color.hue)
    s_gen = pgen.ConstantPG(1.0)
    b_gen = pgen.ConstantPG(1.0)
    return HSBColorGenerator(h_gen, s_gen, b_gen)

def test_color_organist_functions_local():

    import time

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
    h_gen = pgen.UniformRandomPG(0.5, 0.5)
    s_gen = pgen.UniformRandomPG(0.5, 0.5)
    b_gen = pgen.ConstantPG(1.0)

    c_gen = HSBColorGenerator(h_gen, s_gen, b_gen)

    co.select_bank('linear')

    for _ in xrange(24):
        col = c_gen.get()
        co.send_color(col)
        time.sleep(0.3)

def test_co_functions_process():

    import time

    ports = mido.get_output_names()
    midi_service = MidiService(ports[0])

    midi_client = midi_service.get_client()

    organ = ColorOrgan(midi_client, 0, 1, {'linear': 0, 'all': 1})

    #c_gen = nice_color_gen_default(cyan())
    c_gen = test_hue_gen(red())

    def add_to_hue(cgen, mod):
        print cgen
        new_center = pgen.wrap(cgen.h_gen.center + mod, 0.0, 1.0)
        cgen.h_gen.center = new_center

    diffusor = pgen.Diffusor(Rate(10.0))
    c_gen = pgen.Twiddle(c_gen, diffusor, add_to_hue)

    note_trig = ClockTrigger(Rate(bpm=240.))

    organist = ColorOrganist(organ, c_gen, note_trig)

    org_ctrl = ColorOrganistPuppeteer(organist)

    with midi_service.run():
        try:
            org_ctrl.start()
            time.sleep(30.0)
        finally:
            org_ctrl.stop()

class InvalidBankError(Exception):
    pass

class RateError(Exception):
    pass

class MidiServiceError(Exception):
    pass

class MidiServiceNotRunning(MidiServiceError):
    pass



if __name__ == '__main__':
    #test_color_organist_functions_local()
    test_co_functions_process()


































