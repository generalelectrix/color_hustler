"""The show runtime environment."""
import time
import traceback
from queue import Empty

import mido

from .organ import ColorOrganist
from .param_gen import Mutator
from .rate import Trigger, Rate
from . import frame_clock


class Show(object):
    """Encapsulate the show runtime environment."""
    def __init__(self, framerate, cmd_queue, resp_queue, midi_port):
        self.render_trigger = Trigger(rate=Rate(hz=framerate), clock=time)

        self.entities = dict()

        # use sets to ensure items are only registered once
        self.organists = set()
        self.mutators = set()

        self.cmd_queue = cmd_queue
        self.resp_queue = resp_queue

        self.midi_port = midi_port

        self.running = False

    def register_entity(self, entity, name):
        """Add a named entity to the show runtime environment.

        This entity will automatically accept standard commands.
        """
        if name in self.entities:
            raise ValueError("Duplicate entity name: {}".format(name))
        self.entities[name] = entity
        if isinstance(entity, ColorOrganist):
            self.organists.add(entity)
        if isinstance(entity, Mutator):
            self.mutators.add(entity)

    def run(self):
        """Run the show application."""
        self.running = True
        # call first tick
        frame_clock.tick()
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
        frame_clock.tick()

        # apply the mutators
        for mutator in self.mutators:
            mutator.mutate()

        # command the organists to play
        for organist in self.organists:
            organist.play(self.midi_port)

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
                err = False
                # try to process the command, if any error just send
                # a reply and continue
                try:
                    resp = self.process_command(cmd)
                except Exception:
                    err = True
                    resp = traceback.format_exc()
                self.resp_queue.put((err, resp))

    def process_command(self, cmd):
        cmd_type, payload = cmd
        if cmd_type == 'stop':
            self.running = False
            return "Show is stopping."

        # otherwise, assume this is a name.property command and try to run it
        name, attr = cmd_type.split('.')
        try:
            entity = self.entities[name]
        except KeyError:
            raise ValueError("No entity with name '{}'.".format(name))

        if not hasattr(entity, attr):
            raise ValueError("{} has no attribute '{}'.".format(name, attr))

        setattr(entity, attr, payload)

        return None
