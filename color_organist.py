"""A player piano for the color organ.

Necessary elements:

Conversion of a color into a midi event in color organ scheme.

Velocity = intensity
Hue = midi note
Use 0 to 127 for maximum expression (still not a lot of colors...)

Saturation: set as a control change before sending the note
"""
import os
import logging
import traceback
import cmd
from Queue import Empty
from multiprocessing import Process, Queue

from contextlib import contextmanager
from functools import wraps

import mido

import param_gen as pgen
from color import Color, HSBColorGenerator
from color import red, green, blue, cyan, magenta, yellow
from rate import Rate, ClockTrigger, WallClock
from name_registry import NameRegistry, named

# control mappings
CC_SAT = 11

# show saving
SHOW_SUFFIX = '.colorg'

class MidiPort(object):
    """Global midi port.  Implemented as a Singleton."""
    __instance = None
    def __new__(cls, port_name=None):
        """Open a named port."""
        if MidiPort.__instance is None:
            if port_name is not None:
                MidiPort.__instance = mido.open_output(port_name)
            else:
                MidiPort.__instance = mido.open_output()
        return MidiPort.__instance

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
    @named
    def __init__(self, name, ctrl_channel, bank_channel, banks=None):
        self.port = MidiPort()
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

class ColorOrganist(object):
    """Class which uses a color stream to play a color organ."""
    @named
    def __init__(self, note_trig, col_gen):
        self.note_trig = note_trig
        self.col_gen = col_gen

    def play(self, organ):
        """Play a color organ if the moment is right."""
        # should this organist play a note?
        if self.note_trig.trigger():
            organ.send_color(self.col_gen.get())

def nice_color_gen_default(start_color):
    """Instance an aesthetically pleasing color generator.

    start_color is an optional color to start the generator with.  At the moment,
    this just sets the initial center of the hue generator.

    Hue is driven by a gaussian with width of 0.1.
    Saturation is driven by a gaussian centered at 1.0 with width 0.2.
    Brightness is driven by a gaussian centered at 1.0 with width 0.2.
    """
    h_gen = pgen.GaussianRandom(start_color.hue, 0.1)
    s_gen = pgen.GaussianRandom(1.0, 0.2)
    b_gen = pgen.GaussianRandom(1.0, 0.2)
    return HSBColorGenerator(h_gen, s_gen, b_gen)

def test_hue_gen(start_color):
    """Return a color generator that produces a constant color."""
    h_gen = pgen.Constant(start_color.hue)
    s_gen = pgen.Constant(1.0)
    b_gen = pgen.Constant(1.0)
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
    h_gen = pgen.UniformRandom(0.5, 0.5, name='hgen')
    s_gen = pgen.UniformRandom(0.5, 0.5, name='sgen')
    b_gen = pgen.Constant(1.0, name='bgen')

    c_gen = HSBColorGenerator(h_gen, s_gen, b_gen, name='cgen')

    co.select_bank('linear')

    for _ in xrange(24):
        col = c_gen.get()
        co.send_color(col)
        time.sleep(0.3)

def test_co_functions_process():

    import time

    ports = mido.get_output_names()
    p = mido.open_output(ports[0])

    organ = ColorOrgan('test organ', p, 0, 1, {'linear': 0, 'all': 1}, name='organ')

    #c_gen = nice_color_gen_default(cyan())
    c_gen = test_hue_gen(red())

    def add_to_hue(cgen, mod):
        new_center = pgen.wrap(cgen.h_gen.center + mod, 0.0, 1.0)
        cgen.h_gen.center = new_center

    diffusor = pgen.Diffusor(Rate(period=60.0), name='diffusor')

    mutator_chain = pgen.MutatorZombieHerd(c_gen, name='mut_chain')
    mutator_chain.append(pgen.Twiddler(diffusor, add_to_hue, name='diffusor twiddler'))

    mod_chain = pgen.ModulationChain(mutator_chain, name='mod_chain')

    note_trig = ClockTrigger(Rate(bpm=240.), 'note_trig')

    organist = ColorOrganist(note_trig, mod_chain, name='organist')

    wc = WallClock()
    wc.tick()
    now = wc.time()
    print NameRegistry()
    while True:
        organist.play(organ)
        time.sleep(0.02)
        wc.tick()
        if wc.time() > now + 20.0:
            break



class Controller(cmd.Cmd):
    # command format: (command type, payload)
    # command types:
    #   'application': control the application (ie quit)
    #       payload formats:
    #           ('quit', _)
    #           ('save', show name)
    #           ('load', show name)
    #           ('list_midi', _)
    #   'show': control show elements
    #       payload formats:
    #           ('list', _)
    #           ('cmd', object name, command string)
    #           ('new', command string)
    #           ('play', organist name)
    #           ('stop', organist name)
    def __init__(self):
        cmd.Cmd.__init__(self)
        print "Color Organist"
        port = MidiPort()
        print "Using midi port {}.".format(port)
        # TODO: add port selection
        #
        #while port is None:
        #    print "Please select a midi port."
        #    print str(mido.get_output_names()) + '\n'
        #    port = readline()
        print "Starting empty show."
        self.cmd_queue = Queue()
        self.resp_queue = Queue()
        show = Show(60., self.cmd_queue, self.resp_queue)
        self.show_process = Process(target=show.run)
        self.show_process.start()
        print "Show is running."
        self.cmdloop()

    def emptyline(self):
        pass

    def handle_command(self, cmd_type, cmd, payload=None, timeout=1.0):
        """Issue a command to the show application and handle the response.
        """
        self.cmd_queue.put((cmd_type, (cmd, payload)))
        try:
            (resp_err, resp) = self.resp_queue.get(timeout=timeout)
        except Empty:
            print "The show did not response to the command {}".format(command.__name__)
            return (True, None)
        else:
            if resp_err:
                print "An error occurred in response to the command {}:".format(command.__name__)
                print resp
            return (resp_err, resp)

    def do_quit(self, _):
        """Quit the application."""
        resp_err, resp = handle_command('appl', 'quit')
        if not resp_err:
            print resp
            self.show_process.join()
            quit()

    def do_save(self, show_name):
        """Save the current state of the show.  Provide the show name.
        If the named show already exists, it will be overwritten.
        """
        resp_err, resp = handle_command('appl', 'save', show_name)
        if not resp_err:
            print "Saved show {}".format(show_name)

    def do_load(self, show_name):
        """Load a named show."""
        resp_err, resp = handle_command('appl', 'load', show_name)
        if not resp_err:
            print "Loaded show {}".format(show_name)

    def do_list(self, _):
        """List all of the named entities in the current show."""
        resp_err, resp = handle_command('show', 'list')
        if not resp_err:
            print resp

    def do_cmd(self, name_and_command):
        """Perform an action on a named entity.

        The format of this command should be name:command_expression which will be evaluated
        in the show environment as name.command_expression
        """
        pieces = name_and_command.split(':')
        try:
            # pull off the name
            name = pieces[0]
            # rejoin the rest of the command
            cmd = ':'.join(pieces[1:])
        except Exception as err:
            print "An exception ocurred during command parsing: {}".format(err)
            return
        else:
            handle_command('show', 'cmd', (name, cmd))

    def do_new(self, cmd):
        """Create a new entity in the show environment.

        Realistically this just eval's whatever you give it.
        """
        handle_command('show', 'new', cmd)

    def do_play(self, name):
        """Command a named color organ to play."""
        handle_command('show', 'play', name)

    def do_stop(self, name):
        """Command a named color organ to stop playing."""
        handle_command('show', 'stop', name)

class SavedShow(object):
    """Encapsulate the data required to save and load a show."""
    def __init__(self, show):
        self.framerate = show.framerate
        self.render_trigger = show.render_trigger
        self.organs = show.organs
        self.name_registry = NameRegistry()

class Show(object):
    """Encapsulate the show runtime environment."""
    def __init__(self, framerate, cmd_queue, resp_queue):
        self.framerate = Rate(hz=framerate)
        self.render_trigger = ClockTrigger(self.framerate, absolute_time=True)

        # use a set to ensure an organ is only being played once
        self.organs = set()

        self.cmd_queue = cmd_queue
        self.resp_queue = resp_queue

        self.running = False

    def save(self, show_name):
        """Serialize this show to a file.

        For now, overwrite.
        """
        filename = show_name + SHOW_SUFFIX
        with open(filename, 'w+') as show_file:
            pickle.dump(SavedShow(self), show_file)

    def load(self, show_name):
        """Load a show from a file.

        Raises ShowLoadError if a loading error occurrs.
        """
        filename = show_name + SHOW_SUFFIX
        try:
            with open(filename, 'r') as show_file:
                show = pickle.load(show_file)
        except Exception as err:
            raise ShowLoadError(err)
        try:
            self.framerate = show.framerate
            self.render_trigger = show.render_trigger
            self.organs = show.organs
            nr = NameRegistry()
            nr.clear()
            nr.update(show.name_registry)
        except Exception as err:
            raise CorruptShowError("An error ocurred while loading a show.\n"
                                   "Running show is likely corrupted, please "
                                   "exit the application and restart.\n"
                                   "Error: {}".format(err))

    def run(self):
        self.running = True
        # instance the wall clock and call first tick
        wc = WallClock()
        wc.tick()
        # application loop
        while True:
            # if we have been instructed to quit, do so
            if not self.running:
                return
            if self.render_trigger.trigger():
                # render this frame to midi

                # command the organs to play
                for organ in self.organs:
                    organ.play()

                # update the wall clock for the next frame
                wc.tick()

            else:
                while True:
                    time_until_trig = self.render_trigger.time_until_trig()

                    # if it is time to trigger, stop the command loop
                    if time_until_trig <= 0.0:
                        break

                    # if we have time left until render, use it to process events
                    try:
                        cmd = self.cmd_queue.get(timeout=time_until_trig*0.95)
                    except Empty:
                        # fine if we didn't get a control event
                        pass
                    else:
                        # try to process the command, if any error just send
                        # a reply and continue
                        err = False
                        try:
                            cmd_type, payload = cmd
                            if cmd_type == 'application':
                                resp = self.process_appl_cmd(payload)
                            elif cmd_type == 'show':
                                resp = self.process_show_cmd(payload)
                        except Exception:
                            err = True
                            resp = traceback.format_exc()
                        self.resp_queue.put((err, resp))


    def process_appl_cmd(self, appl_cmd):
        cmd_type, payload = appl_cmd
        if cmd_type == 'quit':
            self.running = False
            return "Show application is quitting."
        elif cmd_type == 'load':
            self.load(payload)
            return "Loaded show {}".format(payload)
        elif cmd_type == 'save':
            self.save(payload)
            return "Saved show {}".format(payload)
        elif cmd_type == 'list_midi':
            return mido.get_output_names()
        return None

    def process_show_cmd(self, show_cmd):
        """show_cmd formats:
            ('list', None)
            ('cmd', (object name, command string))
            ('new', command string)
            ('play', organist name)
            ('stop', organist name)

        Returns any response object or None if the command did not require a
        responde.
        """
        cmd_type, payload = show_cmd
        if cmd_type == 'list':
            # return a list of the current named objects
            return NameRegistry().keys()
        elif cmd_type == 'cmd':
            # call a command on an existing object
            name, cmd_str = payload
            # get the named object and call the command on it
            full_cmd = 'NameRegistry()[{}].{}'.format(name, cmd_str)
            eval(full_cmd)
        elif cmd_type == 'new':
            # create a new named object, or really uhh execute arbitrary code lol
            eval(payload)
        elif cmd_type == 'play':
            # add an existing organ to the list of playing organs
            organ = NameRegistry()[payload]
            if not isinstance(organ, ColorOrgan):
                raise TypeError("Received a play command for {}, which is of type"
                                "{} but must be a color organ!".format(payload, type(organ)))
            self.organs.add(organ)
        elif cmd_type == 'stop':
            # stop a playing organ
            organ = NameRegistry()[payload]
            if not isinstance(organ, ColorOrgan):
                raise TypeError("Received a stop command for {}, which is of type"
                                "{} but must be a color organ!".format(payload, type(organ)))
            self.organs.discard(organ)
        return None


class InvalidBankError(Exception):
    pass

class RateError(Exception):
    pass

class MidiServiceError(Exception):
    pass

class MidiServiceNotRunning(MidiServiceError):
    pass

class NoResponseFromShowError(Exception):
    pass

class ShowLoadError(Exception):
    pass

class ShowDoesNotExist(ShowLoadError):
    pass

class CorruptShowError(ShowLoadError):
    pass


if __name__ == '__main__':
    #test_color_organist_functions_local()
    #test_co_functions_process()
    Controller()


































