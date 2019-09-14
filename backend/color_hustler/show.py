"""The show runtime environment."""
import time
import traceback
from queue import Empty, Queue

import mido

from .rate import Trigger, Rate
from . import frame_clock


class Show(object):
    """Encapsulate the show runtime environment."""
    def __init__(self, framerate, midi_port, dmx_port=None):
        frame_clock.tick()
        self.render_trigger = Trigger(rate=Rate(hz=framerate), clock=time)

        self.entities = dict()
        self.organists = set()
        self.gobo_hustler = None
        self.dmx_port = dmx_port

        self.cmd_queue = Queue()
        # callables that are passed command responses
        self.responders = []

        self.midi_port = midi_port

        self.running = False
        self.debug = False

    def register_entity(self, entity, name):
        """Add a named entity to the show runtime environment.

        This entity will automatically accept standard commands.
        """
        if name in self.entities:
            raise ValueError("Duplicate entity name: {}".format(name))
        if not hasattr(entity, 'set_parameter'):
            raise ValueError("{} is not controllable.".format(entity))
        self.entities[name] = entity

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

        # command the organists to play
        for organist in self.organists:
            organist.play(self.midi_port)

        if self.gobo_hustler is not None and self.dmx_port is not None:
            self.gobo_hustler.render(self.dmx_port.dmx_frame)
            if self.debug:

                print(self.dmx_port.dmx_frame[449:])
            self.dmx_port.render()

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
                try:
                    resp = self.process_command(cmd)
                except Exception:
                    resp = ('error', traceback.format_exc())

                if resp is not None:
                    for respond in self.responders:
                        respond(resp)

    def process_command(self, cmd):
        cmd_type, payload = cmd

        if self.debug:
            print("Handling command", cmd)

        if cmd_type == 'stop':
            self.running = False
            return 'message', "Show is stopping."

        if cmd_type == 'list':
            return 'message', "Show entities: {}".format(", ".join(self.entities))

        if cmd_type == 'debug':
            self.debug = payload
            return 'message', "Debug: {}".format(payload)

        # otherwise, assume this is a name.property command and try to run it
        name, parameter = cmd_type.split('.')
        try:
            entity = self.entities[name]
        except KeyError:
            return 'message', "No entity with name '{}'.".format(name)

        entity.set_parameter(parameter, payload)
        return None
