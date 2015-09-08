import time

from name_registry import register_name, get

class Rate(object):
    """Helper class for working with rates."""
    def __init__(self, bpm=None, hz=None, period=None):
        """Create a new rate.

        Must supply exactly one named optional argument {bpm, hz, period}.
        """
        self.hz = None

        if bpm is not None:
            self.bpm = bpm
        elif hz is not None:
            self.hz = hz
        elif period is not None:
            self.period = period
        else:
            raise RateError("Must supply at least one argument to Rate().")

    @property
    def bpm(self):
        return self.hz * 60.0

    @bpm.setter
    def bpm(self, bpm):
        self.hz = bpm / 60.0

    @property
    def period(self):
        return 1.0 / self.hz

    @period.setter
    def period(self, period):
        self.hz = 1.0 / period

class FrameClock(object):
    """Source of universal frame time."""
    @register_name
    def __init__(self):
        # don't set the initial time without ticking once
        self.now = None

    def tick(self):
        self.now = time.time()

    def time(self):
        return self.now

class SystemClock(object):
    """Helper object to enable pickling."""
    @register_name
    def __init__(self):
        pass
    def time(self):
        return time.time()

class ClockTrigger(object):
    """Polling-based scheduling of an operation."""
    @register_name
    def __init__(self, rate, clock_name='frame clock'):
        """Create a new ClockTrigger.

        This trigger will initially be in a state where it will fire immediately
        when first polled.

        Uses the name registration system to get the clock.
        """
        self.rate = rate
        self.clock = get(clock_name)
        self.last_trig = self.clock.time() - self.period

    @property
    def period(self):
        return self.rate.period

    def reset(self):
        """Reset the trigger timer to now."""
        self.last_trig = self.clock.time()

    def trigger(self):
        """Return True if it is time to trigger and reset trigger clock."""
        if self.overdue():
            self.reset()
            return True
        else:
            return False

    def overdue(self):
        """Return True is at least one period has passed since the last trigger."""
        return True if self.time_until_trig() <= 0.0 else False

    def time_until_trig(self):
        """Return the time until the next trigger event.

        If this trigger hasn't fired but is overdue, return a negative time.
        """
        return self.period - (self.clock.time() - self.last_trig)

    def block_until_trig(self):
        """Block thread execution until the next trigger event."""
        while True:
            time_until_trig = self.time_until_trig()
            if time_until_trig <= 0.0:
                # time to trigger
                break
            else:
                # wait 95% of the remaining time and run again
                time.sleep(0.95*time_until_trig)

class RateError(Exception):
    pass
