"""The show runtime environment."""
import traceback
from queue import Empty

import mido

from .organ import *
from .rate import Trigger, Rate
from .color import *
from .param_gen import *
from . import frame_clock

import time

class Show(object):
    """Encapsulate the show runtime environment."""
    def __init__(self, framerate, cmd_queue, resp_queue):
        self.render_trigger = Trigger(rate=Rate(hz=framerate), clock=time)

        # use sets to ensure items are only registered once
        self.organists = set()
        self.mutators = set()

        self.cmd_queue = cmd_queue
        self.resp_queue = resp_queue

        self.running = False

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
        # apply the mutators
        for mutator in self.mutators:
            mutator.mutate()

        # command the organists to play
        for organist in self.organists:
            organist.play()

        # update the frame clock for the next frame
        frame_clock.tick()


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
                    raise NotImplementedError("Come back and implement a command layer.")
                except Exception:
                    err = True
                    resp = traceback.format_exc()
                self.resp_queue.put((err, resp))
