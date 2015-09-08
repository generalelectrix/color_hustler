"""Main application."""
import os
import logging
import traceback
import cmd
from Queue import Queue, Empty
from threading import Thread
import dill as pickle

import mido

from name_registry import get

# global wildcard imports to enable interactive object creation in one namespace
# I'm so sorry.
from color_organist import *
from rate import *
from color import *
from param_gen import *

from operator import add, sub, div, mod, mul

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
        print "Using midi port {}.".format(mido.get_output_names()[0])
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
        self.show_thread = Thread(target=show.run)
        self.show_thread.start()
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
            print "The show did not response to the command '{} {}'".format(cmd, payload)
            return (True, None)
        else:
            if resp_err:
                print "An error occurred in response to the command '{} {}':".format(cmd, payload)
                print resp
            return (resp_err, resp)

    def do_quit(self, _):
        """Quit the application."""
        resp_err, resp = self.handle_command('appl', 'quit')
        if not resp_err:
            print resp
            self.show_thread.join()
            quit()

    def do_save(self, show_name):
        """Save the current state of the show.  Provide the show name.
        If the named show already exists, it will be overwritten.
        """
        resp_err, resp = self.handle_command('appl', 'save', show_name)
        if not resp_err:
            print "Saved show {}".format(show_name)

    def do_load(self, show_name):
        """Load a named show."""
        resp_err, resp = self.handle_command('appl', 'load', show_name)
        if not resp_err:
            print "Loaded show {}".format(show_name)

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
            print "Invalid filter: {}".format(item_filter)
            return
        resp_err, items = self.handle_command('show', 'list')
        if not resp_err:
            type_filters = type_map[item_filter]
            for name, kind in items:
                for type_filter in type_filters:
                    if issubclass(kind, type_filter):
                        print str(name) + ': ' + str(kind)
                        break



    def do_cmd(self, name_and_command):
        """Perform an action on a named entity.

        The format of this command should be name.command_expression which will be evaluated
        in the show environment as name.command_expression
        """
        pieces = name_and_command.split('.')
        try:
            # pull off the name
            name = pieces[0]
            # rejoin the rest of the command
            cmd = '.'.join(pieces[1:])
        except Exception as err:
            print "An exception ocurred during command parsing: {}".format(err)
            return
        else:
            resp_err, resp = self.handle_command('show', 'cmd', (name, cmd))
            if not resp_err and resp is not None:
                print resp


    def do_new(self, cmd):
        """Create a new entity in the show environment.

        Realistically this just eval's whatever you give it.
        """
        resp_err, resp = self.handle_command('show', 'new', cmd)

    def do_play(self, name):
        """Command a named color organ to play."""
        resp_err, resp = self.handle_command('show', 'play', name)

    def do_stop(self, name):
        """Command a named color organ to stop playing."""
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
                    line = line.rstrip()
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
            print "An error occurred during script execution, line {}\n".format(n)
            print err

class SavedShow(object):
    """Encapsulate the data required to save and load a show."""
    def __init__(self, show):
        self.frame_clock = show.frame_clock
        self.render_trigger = show.render_trigger
        self.organists = show.organists
        self.name_registry = NameRegistry()

class Show(object):
    """Encapsulate the show runtime environment."""
    def __init__(self, framerate, cmd_queue, resp_queue):
        self.system_clock = SystemClock(name='system clock')
        self.render_trigger = Trigger(Rate(hz=framerate), 'system clock')

        # use a set to ensure an organist is only playing once
        self.organists = set()

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
            nr = NameRegistry()
            nr.clear()
            nr.update(show.name_registry)
        except Exception as err:
            raise CorruptShowError("An error ocurred while loading a show.\n"
                                   "Running show is likely corrupted, please "
                                   "exit the application and restart.\n"
                                   "Error: {}".format(err))

    def run(self):

        import color as col
        import rate
        import param_gen as pgen

        port = MidiPort()

        self.running = True
        # instance the frame clock and call first tick
        self.frame_clock = FrameClock(name='frame clock')
        self.frame_clock.tick()
        # application loop
        while True:
            # if we have been instructed to quit, do so
            if not self.running:
                return
            if self.render_trigger.trigger():
                # render this frame to midi

                # command the organists to play
                for organist in self.organists:
                    organist.play()

                # update the frame clock for the next frame
                self.frame_clock.tick()

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
                            if cmd_type == 'appl':
                                resp = self.process_appl_cmd(payload)
                            elif cmd_type == 'show':
                                resp = self.process_show_cmd(payload)
                            else:
                                err = True
                                resp = "Show received nknown command type {}".format(cmd_type)
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
            # create a new named object, or really uhh execute arbitrary code lol
            exec(payload)
        elif cmd_type == 'play':
            # add an existing organ to the list of playing organs
            organist = get(payload)
            if not isinstance(organist, ColorOrganist):
                raise TypeError("Received a play command for {}, which is of type"
                                "{} but must be a color organist!".format(payload, type(organist)))
            self.organists.add(organist)
        elif cmd_type == 'stop':
            # stop a playing organ
            organist = get(payload)
            if not isinstance(organist, ColorOrganist):
                raise TypeError("Received a stop command for {}, which is of type"
                                "{} but must be a color organ!".format(payload, type(organist)))
            self.organists.discard(organist)
        return None

class NoResponseFromShowError(Exception):
    pass

class ShowLoadError(Exception):
    pass

class ShowDoesNotExist(ShowLoadError):
    pass

class CorruptShowError(ShowLoadError):
    pass

if __name__ == '__main__':
    Controller()