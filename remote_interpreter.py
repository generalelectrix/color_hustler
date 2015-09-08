"""Module providing tools for running a interpreter emulator in another thread.

Ensures responsiveness of the UI with buffered communication with the main
thread.

Components of this module:
- The entity living on the model side which drains the control queue, processes
commands, and sends replies back to the view side.

- The entity living on the view side which runs a read loop, buffers input
controls, and provides feedback on responses.  Ideally this should be a very
small GUI application.
"""
import Tkinter as tk

class RemoteInterpreter(tk.Frame):
    def __init__(self, master=None):
        tk.Frame.__init__(self, master)
        self.grid()
        self.create_widgets()

    def create_widgets(self):
        self.console_contents = tk.StringVar()
        self.console = tk.Message(self, textvariable=self.console_contents)
        self.terminal = tk.Button(self, text='Quit',
            command=self.quit)
        self.quitButton.grid()

app = Application()
app.master.title('Sample application')
app.mainloop()

class RemoteInterpreter(object):
    """Encapsulation of the user-side of the remote interpreter control."""
