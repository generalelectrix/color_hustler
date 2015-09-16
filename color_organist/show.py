"""The show runtime environment."""
import traceback
from Queue import Empty

import mido

# use dill to enable pickling lambdas
import dill as pickle

from name_registry import NameRegistry
from rate import SYS_CLOCK_NAME, FRAME_CLOCK_NAME

# global wildcard imports to enable interactive object creation in one namespace
# I'm so sorry.
from organ import *
from rate import *
from color import *
from param_gen import *

from operator import add, sub, div, mod, mul

class SavedShow(object):
    """Encapsulate the data required to save and load a show."""
    def __init__(self, show):
        self.frame_clock = show.frame_clock
        self.render_trigger = show.render_trigger
        self.organists = show.organists
        self.mutators = show.mutators
        self.name_registry = NameRegistry()

class Show(object):
    """Encapsulate the show runtime environment."""
    def __init__(self, framerate, cmd_queue, resp_queue):
        self.system_clock = SystemClock(name=SYS_CLOCK_NAME)
        self.render_trigger = Trigger(Rate(hz=framerate), SYS_CLOCK_NAME)

        # use sets to ensure items are only registered once
        self.organists = set()
        self.mutators = set()

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
            self.frame_clock = show.frame_clock
            self.render_trigger = show.render_trigger
            self.organists = show.organists
            self.mutators = show.mutators
            nr = NameRegistry()
            nr.clear()
            nr.update(show.name_registry)
        except Exception as err:
            raise ShowLoadError("An error ocurred while loading a show.\n"
                                   "Running show is likely corrupted, please "
                                   "exit the application and restart.\n"
                                   "Error: {}".format(err))

    def run(self):
        """Run the show application."""

        self.running = True
        # instance the frame clock and call first tick
        self.frame_clock = FrameClock(name=FRAME_CLOCK_NAME)
        self.frame_clock.tick()
        # application loop
        while True:
            # if we have been instructed to quit, do so
            if not self.running:
                return
            if self.render_trigger.trigger():
                # render this frame to midi
                self.render()

            else:
                # we are not ready to draw a frame, process show commands
                self.process_commands_until_render()

    def render(self):
        """Render the current frame to midi."""
        # apply the mutators
        for mutator in self.mutators:
            mutator.mutate()

        # command the organists to play
        for organist in self.organists:
            organist.play()

        # update the frame clock for the next frame
        self.frame_clock.tick()


    def process_commands_until_render(self):
        """Use any remaining time until rendering a frame to handle commands."""
        while True:
            time_until_render = self.render_trigger.time_until_trig()
            # if it is time to render, stop the command loop
            if time_until_render <= 0.0:
                break

            # process control events
            try:
                # time out slightly before render time to improve framerate stability
                cmd = self.cmd_queue.get(timeout=time_until_render*0.95)
            except Empty:
                # fine if we didn't get a control event
                pass
            else:
                # try to process the command, if any error just send
                # a reply and continue
                err = False
                try:
                    cmd_type, payload = cmd
                    if cmd_type == 'appl':
                        resp = self.process_appl_cmd(payload)
                    elif cmd_type == 'show':
                        resp = self.process_show_cmd(payload)
                    else:
                        err = True
                        resp = "Show received unknown command type {}".format(cmd_type)
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
            return [ (key, type(val)) for key, val in NameRegistry().iteritems()]
        elif cmd_type == 'cmd':
            # call a command on an existing object
            name, cmd_str = payload
            # get the named object and call the command on it
            full_cmd = "get('{}').{}".format(name, cmd_str)
            exec(full_cmd)
        elif cmd_type == 'new':
            # create a new named object, or really uhh execute arbitrary code
            exec(payload)
        elif cmd_type == 'run':
            # register an organ or mutator with the runtime
            item = get(payload)
            if isinstance(item, ColorOrganist):
                self.organists.add(item)
            elif isinstance(item, Mutator):
                self.mutators.add(item)
            else:
                raise TypeError("Received a run command for {}, which is of type"
                "{} but must be and organist or mutator!".format(payload, type(item)))
        elif cmd_type == 'stop':
            # register an organ or mutator with the runtime
            item = get(payload)
            if isinstance(item, ColorOrganist):
                self.organists.discard(item)
            elif isinstance(item, Mutator):
                self.mutators.discard(item)
            else:
                raise TypeError("Received a stop command for {}, which is of type"
                "{} but must be and organist or mutator!".format(payload, type(item)))
        return None

class ShowLoadError(Exception):
    pass