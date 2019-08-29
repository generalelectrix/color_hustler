"""Main show application.

Main thread runs the command loop using the cmd module.  This thread owns another
thread which handles processing show commands and rendering output to midi.

Unfortunately, due to some ctypes thing, using the mido library in multiple true
processes is difficult or impossible, so we're still bound by the GIL.
"""
import traceback
import cmd
from queue import Queue, Empty
from threading import Thread

import mido

from .show import Show

from .organ import ColorOrgan, ColorOrganist
#from hue_organ import HueOrgan
from .param_gen import ParameterGenerator, Modulator, Mutator, FXChain
from .color import ColorGenerator
from .rate import Trigger

class Controller(cmd.Cmd):
    """cmd module style show controller.

    Owns the show runtime environment thread.
    """
    def __init__(self):
        cmd.Cmd.__init__(self)
        print("Color Organist")
        print("Using midi port {}.".format(mido.get_output_names()[0]))
        # TODO: add port selection, mido makes this tricky because it doesn't
        # play nicely with threads.
        #
        #while port is None:
        #    print "Please select a midi port."
        #    print str(mido.get_output_names()) + '\n'
        #    port = readline()
        print("Starting empty show.")
        self.cmd_queue = Queue()
        self.resp_queue = Queue()
        show = Show(60., self.cmd_queue, self.resp_queue)
        self.show_thread = Thread(target=show.run)
        self.show_thread.start()
        print("Show is running.")
        self.cmdloop()

    def emptyline(self):
        pass

    def handle_command(self, cmd_type, cmd, payload=None, timeout=1.0):
        """Issue a command to the show application and handle the response.
        """
        # command format: (command type, payload)
        # command types:
        #   'application': control the application (ie quit)
        #       payload formats:
        #           ('quit', _)
        #           ('save', show name)
        #           ('load', show name)
        #   'show': control show elements
        #       payload formats:
        #           ('list', _)
        #           ('cmd', object name, command string)
        #           ('new', command string)
        #           ('run', mutator or organist name)
        #           ('stop', mutator or organist name)
        self.cmd_queue.put((cmd_type, (cmd, payload)))
        try:
            (resp_err, resp) = self.resp_queue.get(timeout=timeout)
        except Empty:
            print("The show did not respond to the command '{} {}'".format(cmd, payload))
            return (True, None)
        else:
            if resp_err:
                print("An error occurred in response to the command '{} {}':".format(cmd, payload))
                print(resp)
            return (resp_err, resp)

    def do_quit(self, _):
        """Quit the application."""
        resp_err, resp = self.handle_command('appl', 'quit')
        if not resp_err:
            print(resp)
            self.show_thread.join()
            quit()

    def do_save(self, show_name):
        """Save the current state of the show.  Provide the show name.
        If the named show already exists, it will be overwritten.
        """
        resp_err, resp = self.handle_command('appl', 'save', show_name)
        if not resp_err:
            print("Saved show {}".format(show_name))

    def do_load(self, show_name):
        """Load a named show."""
        resp_err, resp = self.handle_command('appl', 'load', show_name)
        if not resp_err:
            print("Loaded show {}".format(show_name))

    def do_list(self, item_filter):
        """List named entities in the current show.

        If no argument is provided, list everything.  Otherwise, filter the list
        based on object type.  Supported types are:
            - orgs (organs and organists)
            - gens (parameter and color generators)
            - mods (modulators and mutators)
            - chains (fx chains)
            - trigs (triggers)
        """
        type_map = {'': [object],
                    'orgs': [ColorOrgan, ColorOrganist],
                    'gens': [ParameterGenerator, ColorGenerator],
                    'mods': [Modulator, Mutator],
                    'chains': [FXChain],
                    'trigs': [Trigger]}

        if item_filter not in type_map:
            print("Invalid filter: {}".format(item_filter))
            return
        resp_err, items = self.handle_command('show', 'list')
        if not resp_err:
            type_filters = type_map[item_filter]
            for name, kind in items:
                for type_filter in type_filters:
                    if issubclass(kind, type_filter):
                        print(str(name) + ': ' + str(kind))
                        break

    def do_cmd(self, name_and_command):
        """Perform an action on a named entity.

        The format of this command should be name.command_expression which will
        be executed in the show environment.
        """
        pieces = name_and_command.split('.')
        try:
            # pull off the name
            name = pieces[0]
            # rejoin the rest of the command
            cmd = '.'.join(pieces[1:])
        except Exception as err:
            print("An exception ocurred during command parsing: {}".format(err))
            return
        else:
            resp_err, resp = self.handle_command('show', 'cmd', (name, cmd))
            if not resp_err and resp is not None:
                print(resp)

    def do_new(self, cmd):
        """Create a new entity in the show environment.

        Realistically this just exec's whatever you give it.
        """
        resp_err, resp = self.handle_command('show', 'new', cmd)

    def do_run(self, name):
        """Command a ColorOrganist or Mutator to run."""
        resp_err, resp = self.handle_command('show', 'run', name)

    def do_stop(self, name):
        """Command a ColorOrganist or Mutator to stop."""
        resp_err, resp = self.handle_command('show', 'stop', name)

    def do_script(self, script_filename):
        """Run a script of commands using this interface.

        Provide this command with the path to the script of commands to be run.
        """
        n = 0
        try:
            with open(script_filename, 'r') as script:
                command = ''
                for n, line in enumerate(script):
                    line = line.rstrip().lstrip()
                    # allow comments
                    if not line.startswith('#'):
                        # enable multi-line using semicolon
                        if line.endswith(';'):
                            command += line[:-1]
                        else:
                            command += line
                            self.onecmd(command)
                            command = ''
                        #TODO: figure out how to stop on an error without quitting
                        # the command loop
                        #if err:
                        #    print "An error occurred, stopping script execution."
                        #    break
        except Exception:
            err = traceback.format_exc()
            print("An error occurred during script execution, line {}\n".format(n))
            print(err)