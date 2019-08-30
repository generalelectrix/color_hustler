"""Show setup for color hustler.

Provides color selection with stochastic variants on each color parameter.
"""
import asyncio
import websockets
import mido
import cmd
import json
from queue import Empty
from threading import Thread
from .color import ColorGenerator
from .organ import ColorOrganist
from .param_gen import Noise
from .rate import Trigger, Rate
from .show import Show


def initialize(midi_port_name, framerate=60.0):
    midi_port = mido.open_output(midi_port_name)

    show = Show(framerate=framerate, midi_port=midi_port)

    def add_random_source(name, center):
        generator = Noise(mode=Noise.GAUSSIAN, center=center, width=0.0)
        show.register_entity(generator, name)
        return generator

    # build modulation chains for each color coordinate
    h_gen = add_random_source('hue', center=0.0)
    s_gen = add_random_source('saturation', center=1.0)
    l_gen = add_random_source('lightness', center=0.5)

    # wire these things up to an organist
    color_gen = ColorGenerator(h_gen=h_gen, s_gen=s_gen, v_gen=l_gen)

    note_trig = Trigger(rate=Rate(hz=1.0))
    show.register_entity(note_trig, 'note_trigger')

    organist = ColorOrganist(ctrl_channel=1, note_trig=note_trig, col_gen=color_gen)
    show.organists.add(organist)

    return show

def run_websocket_server(port, cmd_queue):
    """Start up a simple websocket server that deserializes messages."""
    async def handle(websocket, path):
        async for message in websocket:
            try:
                payload = json.loads(message, parse_int=float)
                print("Handling message", payload)
            except ValueError:
                print("Could not deserialize message as json:", message)
                continue
            cmd_queue.put(payload)

    asyncio.set_event_loop(asyncio.new_event_loop())

    start_server = websockets.serve(handle, "localhost", port)
    asyncio.get_event_loop().run_until_complete(start_server)
    asyncio.get_event_loop().run_forever()
    # FIXME no quit mechanism

class Controller(cmd.Cmd):
    """cmd module style show controller.
    Owns the show runtime environment thread.
    """
    def __init__(self):
        cmd.Cmd.__init__(self)
        print("Color Organist")
        port_name = mido.get_output_names()[0]
        print("Using midi port {}.".format(port_name))

        show = initialize(port_name)

        self.cmd_queue = show.cmd_queue
        self.resp_queue = show.resp_queue

        # launch the websocket server
        self.socket_thread = Thread(
            target=lambda: run_websocket_server(4321, show.cmd_queue))
        self.socket_thread.start()

        self.show_thread = Thread(target=show.run)
        self.show_thread.start()
        print("Show is running.")
        self.cmdloop()

    def emptyline(self):
        pass

    def handle_command(self, cmd_type, payload=None, timeout=1.0):
        """Issue a command to the show application and handle the response."""
        self.cmd_queue.put((cmd_type, payload))
        try:
            (resp_err, resp) = self.resp_queue.get(timeout=timeout)
        except Empty:
            print("The show did not respond to the command '{} {}'".format(cmd_type, payload))
            return (True, None)

        if resp_err:
            print("An error occurred in response to the command '{} {}':".format(cmd, payload))
        print(resp)

    def do_quit(self, _):
        """Quit the application."""
        self.handle_command('stop')
        self.show_thread.join()
        quit()

    def do_list(self, _):
        """List named entities in the current show."""
        self.handle_command('list')

    def do_cmd(self, name_and_command):
        """Perform an action on a named entity."""
        try:
            cmd_type, payload = eval(name_and_command)
        except Exception as err:
            print("error:", err)
        self.handle_command(cmd_type, payload)
