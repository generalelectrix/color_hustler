# Global source of current frame time.
# FIXME: move this into the top-level show and inject it into clients.
# This is a stopgap put in place to ease refactoring.
import time as systime

# don't set the initial time without ticking once
_now = None

def time():
    global _now
    return _now

def tick():
    global _now
    _now = systime.time()