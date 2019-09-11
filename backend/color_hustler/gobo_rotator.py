"""Fixture driver for various gobo rotators."""

"""
--- GOBO SPINNAZ ---

(DHA Varispeed driven by GOBO SPINNAZ driver)

Unsurprisingly, straight as an arrow, given linear voltage drive of a DC motor.
Max speed is MUCH slower than the other two rotator styles.

[
    (15, 0.0075),
    (35, 0.0225),
    (55, 0.0377),
    (75, 0.0523),
    (95, 0.0669),
    (115, 0.0825),
    (135, 0.0963),
    (155, 0.111),
    (175, 0.127),
    (195, 0.141),
    (215, 0.156),
    (235, 0.17),
    (255, 0.185),
]

If we normalize speed so the fastest rotator at max is 1, we lose a lot of the
upper range and resolution of the faster rotators.  I think I'll scale them so
that the slowest rotator's max speed is 1.0, but make the profiles understand
control signals outside of 1.0 if we want to reach up to higher values.

1.0 thus means 0.185 Hz or 11.1 rpm.
"""
from bisect import bisect_left

UNIT_SPEED = 0.185 # Hz

class GoboSpinna:
    """Control profile for custom DHA Varispeed driven by GOBO SPINNAZ.

    Channel layout:
    0: gobo 1 direction
    1: gobo 1 speed
    2: gobo 2 direction
    3 gobo 2 speed
    """
    def __init__(self, address):
        self.address = address
        self.g0 = 0.0
        self.g1 = 0.0

    def render(self, buf):
        d0, s0 = self._render_single(self.g0)
        d1, s1 = self._render_single(self.g1)
        buf[self.address] = d0
        buf[self.address + 1] = s0
        buf[self.address + 2] = d1
        buf[self.address + 3] = s1

    def _render_single(self, value):
        direction = 0 if value <= 0.0 else 255
        speed_int = int(abs(value) * 256.0)
        return direction, min(max(speed_int, 0), 255)


class LookupTable:
    """Use a lookup table to set DMX values based on selected unit speed."""
    speeds, dmx_vals = [], []

    def __init__(self, address):
        self.address = address
        self.value = 0.0

    def render(self, buf):
        buf[self.address] = lookup_dmx_val(self.speeds, self.dmx_vals, self.value)
        buf[self.address+1] = 0
"""
--- Roto-Q DMX ---
0: stopped

Max speed: DMX value 1, about 0.43 rot/sec
It looks like several values are bucketed to the same speed:
3 4 5
6 7
8 9 10
11 12
14 15
16 17
19 20

255 254
252 251 250
249 248
247 246 245
244 243
241 240
239 238
236 235

These are all above unit speed, so fine to ignore them.

There's no actual DMX value in the center for no rotation. 127 and 128 are each
the slowest value for each rotation direction.  This explains some things.
"""

ROTO_Q_MEAS = [
    (128, 0.00479),
    (137, 0.01),
    (147, 0.0169),
    (157, 0.03),
    (167, 0.0454),
    (177, 0.063),
    (187, 0.0792),
    (197, 0.106),
    (207, 0.1425),
    (217, 0.177),
    (227, 0.242),
    (237, 0.308),
    (242, 0.345),
    (249, 0.3875),
    (255, 0.43),
]

def roto_q_lut():
    # upper range
    lut = build_lut(ROTO_Q_MEAS)

    # invert to create LUT for lower range
    # the lower range has one fewer DMX value than the upper range
    # the min and max speeds are the same, though, so we'll need to arbitrarily
    # pick a value from the upper range to remove.  One of the duplicated values
    # makes the most sense, as the interpolated values are just plain wrong for
    # those anyway.
    first_section = lut[:-5]
    second_section = [(s, v-1) for s, v in lut[-4:]]
    reverse_lut = list(reversed(list((-1*s, -1*v) for s, v in (first_section + second_section))))
    assert len(reverse_lut) == len(lut) - 1

    # offset the coordinates, add the center detent, and done
    speeds, dmx_vals = [], []
    for s, v in reverse_lut:
        speeds.append(s)
        dmx_vals.append(127 + v)
    speeds.append(0.0)
    dmx_vals.append(0)
    for s, v in lut:
        speeds.append(s)
        dmx_vals.append(128 + v)
    return speeds, dmx_vals


class RotoQDmx:
    """Control profile for Apollo Roto-Q DMX.

    Channel layout:
    0: direction/speed
    1: set to 0 for rotation mode
    """
    speeds, dmx_vals = roto_q_lut()

    def __init__(self, address):
        self.address = address
        self.value = 0.0

    def render(self, buf):
        buf[self.address] = lookup_dmx_val(self.speeds, self.dmx_vals, self.value)
        buf[self.address+1] = 0


"""
--- Smart Move DMX ---

Bucketed speeds:
5 6 7 8
18 19
251 250 249 248
238 237

Slowest: 124, 133
Stopped: 125-132
"""
# This shit is bananas, super-weird speed profile.
SMART_MOVE_MEAS = [
    (135, 0.00193),
    (145, 0.0027),
    (155, 0.00583),
    (165, 0.0102),
    (175, 0.0175),
    (176, 0.0194),
    (179, 0.0244),
    (181, 0.0306),
    (183, 0.0406),
    (184, 0.0481),
    (185, 0.0604),
    (187, 0.0794),
    (189, 0.0909),
    (191, 0.0972),
    (193, 0.107),
    (195, 0.116),
    (205, 0.141),
    (215, 0.166),
    (225, 0.191),
    (235, 0.223),
    (245, 0.27),
    (249, 0.293),
    (255, 0.344),
]

def lookup_dmx_val(speeds, dmx_vals, speed):
    """Lookup appropriate dmx value using speed lookup table."""
    index = bisect_left(speeds, speed)
    if index == 0:
        return dmx_vals[0]
    if index == len(dmx_vals):
        return dmx_vals[-1]
    if speeds[index] - speed < speed - speeds[index-1]:
       return dmx_vals[index]
    else:
       return dmx_vals[index-1]


def build_lut(meas):
    v = [m[0] for m in meas]
    s = [m[1]/UNIT_SPEED for m in meas]

    ds_dv = [ds/dv for ds, dv in zip(delta(s), delta(v))]

    min_value = v[0]

    values = []
    for value in range(v[0], v[-1]+1):
        base_s, base_v, base_ds_dv = s[0], v[0], ds_dv[0]
        for v0, s0, ds0 in zip(v, s, ds_dv):
            if value - v0 < 0:
                break
            base_s, base_v, base_ds_dv = s0, v0, ds0


        speed = base_s + (value - base_v)*base_ds_dv

        values.append((speed, value - min_value))
    return values

def delta(vals):
    return [h - l for l, h in zip(vals, vals[1:])]


































