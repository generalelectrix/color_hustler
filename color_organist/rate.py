"""Entities relating to the progression of time."""
import time

class Rate(object):
    """Helper class for working with rates."""
    def __init__(self, bpm=None, hz=None, period=None):
        """Create a new rate.

        Must supply exactly one named optional argument {bpm, hz, period}.
        """
        self._hz = None

        if bpm is not None:
            self.bpm = bpm
        elif hz is not None:
            self.hz = hz
        elif period is not None:
            self.period = period
        else:
            raise TypeError("Must supply at least one argument to Rate().")

    @property
    def hz(self):
        return self._hz

    @hz.setter
    def hz(self, hz):
        self._hz = float(hz)

    @property
    def bpm(self):
        return self.hz * 60.0

    @bpm.setter
    def bpm(self, bpm):
        self.hz = float(bpm) / 60.0

    @property
    def period(self):
        return 1.0 / self.hz

    @period.setter
    def period(self, period):
        self.hz = 1.0 / float(period)

class Trigger(object):
    """Polling-based scheduling of an operation."""
    def __init__(self, rate, clock=None):
        """Create a new Trigger.

        This trigger will initially be in a state where it will fire immediately
        when first polled.

        Uses the name registration system to get the clock.
        """
        self._rate = rate
        if clock is None:
            from . import frame_clock as clock

        self.clock = clock
        self.last_trig = clock.time() - self.period

    @property
    def period(self):
        return self._rate.period

    @period.setter
    def period(self, period):
        self._rate.period = period

    @property
    def hz(self):
        return self._rate.hz

    @hz.setter
    def hz(self, hz):
        self._rate.hz = hz

    @property
    def bpm(self):
        return self._rate.bpm

    @bpm.setter
    def bpm(self, bpm):
        self._rate.bpm = bpm

    def trigger(self):
        """Return True if it is time to trigger, and reset trigger clock."""
        now = self.clock.time()
        if self._time_until_trig(now) <= 0.0:
            self.last_trig = now
            return True
        return False

    def time_until_trig(self):
        """Return the time until the next trigger event.

        If this trigger hasn't fired but is overdue, return a negative time.
        """
        return self._time_until_trig(self.clock.time())

    def _time_until_trig(self, now):
        """Return the time until the next trigger event.

        Use a time passed in for consistency across a single method call if
        this trigger is being driven by the system clock.
        """
        return self.period - (now - self.last_trig)

