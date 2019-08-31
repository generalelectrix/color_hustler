"""Show setup for color hustler.

Provides color selection with stochastic variants on each color parameter.
"""
import asyncio
import concurrent.futures
import websockets
import mido
import cmd
import json
from queue import Empty, Queue
from threading import Thread
from .color import ColorGenerator
from .organ import ColorOrganist
from .param_gen import Noise, ConstantList, Modulator
from .rate import Trigger, Rate
from .show import Show

def initialize(midi_port_name, framerate=60.0):
    midi_port = mido.open_output(midi_port_name)

    show = Show(framerate=framerate, midi_port=midi_port)

    def add_random_source(name, center):
        generator = Noise(mode=Noise.GAUSSIAN, center=center, width=0.0)
        show.register_entity(generator, name)
        return generator

    def create_chain(index):
        def label(name):
            return name + str(index)


        # build modulation chains for each color coordinate
        h_gen = add_random_source(label('hue'), center=0.0)
        s_gen = add_random_source(label('saturation'), center=1.0)
        l_gen = add_random_source(label('lightness'), center=0.5)

        # allow constant list modulation of hue
        hue_offset_list = ConstantList([0.0])
        show.register_entity(hue_offset_list, label('hue_offsets'))

        offset_hue = Modulator(source=h_gen, modulation_gen=hue_offset_list)
        show.register_entity(offset_hue, label('hue_modulator'))

        color_gen = ColorGenerator(h_gen=offset_hue, s_gen=s_gen, v_gen=l_gen)

        note_trig = Trigger(rate=Rate(bpm=60.0))
        show.register_entity(note_trig, label('trigger'))
        organist = ColorOrganist(ctrl_channel=index, note_trig=note_trig, col_gen=color_gen)
        show.organists.add(organist)

    create_chain(0)
    create_chain(1)
    create_chain(2)

    return show

def run_websocket_server(port, cmd_queue, resp_queue):
    """Start up a simple websocket server that deserializes messages."""
    # Use a thread pool to concurrently poll the blocking response queue.
    executor = concurrent.futures.ThreadPoolExecutor(max_workers=1)

    async def handle_command(websocket, path):
        async for message in websocket:
            try:
                payload = json.loads(message)
            except ValueError:
                print("Could not deserialize message as json:", message)
                continue

            cmd_queue.put(payload)

    async def handle_response(websocket, path):
        event_loop = asyncio.get_event_loop()
        while True:
            message = await event_loop.run_in_executor(executor, resp_queue.get)
            await websocket.send(json.dumps(message))

    async def handle(websocket, path):
        tasks = [
            asyncio.create_task(c)
            for c in [
                handle_command(websocket, path),
                handle_response(websocket, path)]]
        done, pending = await asyncio.wait(tasks, return_when=asyncio.FIRST_COMPLETED)

        for task in pending:
            task.cancel()

    asyncio.set_event_loop(asyncio.new_event_loop())

    event_loop = asyncio.get_event_loop()

    start_server = websockets.serve(handle, "localhost", port)
    event_loop.run_until_complete(start_server)
    event_loop.run_forever()

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

        # fan the show responses out to the command line and the frontend
        # use a fake queue that just prints synchronously to report to the command line
        frontend_queue = Queue()
        def show_resp(resp):
            try:
                resp_type, payload = resp
            except ValueError:
                print("Error when unpacking the show response", resp)
            else:
                if resp_type in ('message', 'error'):
                    print(payload)

        show.responders = [frontend_queue.put, show_resp]

        # launch the websocket server
        self.socket_thread = Thread(
            target=lambda: run_websocket_server(4321, show.cmd_queue, frontend_queue))
        self.socket_thread.start()

        self.show_thread = Thread(target=show.run)
        self.show_thread.start()
        print("Show is running.")
        self.cmdloop()

    def emptyline(self):
        pass

    def handle_command(self, cmd_type, payload=None):
        """Issue a command to the show application and handle the response."""
        self.cmd_queue.put((cmd_type, payload))

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
            return
        self.handle_command(cmd_type, payload)
