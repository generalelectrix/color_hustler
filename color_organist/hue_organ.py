"""Primitive color organ implementation feeding hue lamps."""
from itertools import cycle
from ip_hue import HueTransmitter
from .name_registry import register_name
from .organ import InvalidBankError

class HueOrgan(object):
    """Takes a stream of colors and sends them to hue lamps."""
    @register_name
    def __init__(self, name, banks, start_bank=None, ttime=None):
        self.banks = banks
        # pick a random bank if we didn't specify one
        self.current_bank = banks.keys()[0] if start_bank is None else banks[start_bank]

        # keep track of where we are in the bank with an iterator
        self.pattern_iter = cycle(self.current_bank)

        # hack for now, depend on the ip_hue package for default setup
        self.lamp_trans = HueTransmitter()

    def send_color(self, color):
        """Send a color message to the next set of hue lamps."""
        lamps = self.pattern_iter.next()
        for lamp in lamps:
            self.lamp_trans.send_color(lamp, color)

    def select_bank(self, bank):
        """Select a named bank."""
        try:
            self.current_bank = self.banks[bank]
            self.pattern_iter = cycle(self.current_bank)
        except KeyError:
            raise InvalidBankError(
                "{} is not a valid bank.  Valid banks are {}"
                .format(bank, self.banks.keys()))