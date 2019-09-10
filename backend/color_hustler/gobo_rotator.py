"""Fixture driver for various gobo rotators.

--- Roto-Q DMX ---
0: stopped

Max speed: DMX value 1, about 0.43 rot/sec
It looks like several values are bucketed to the same speed.  Buckets:
1
2
3 4 5
6 7
8 9 10
11 12
13
14 15
16 17
18
19 20
the remainder seem to be singlets

On the upper end:
255 254
253
252 251 250
249 248
247 246 245
244 243
242
241 240
239 238
237
236 235
singlets below

There's no actual DMX value in the center for no rotation. 127 and 128 are each
the slowest value for each rotation direction.  This explains some things...

Measurements:
[
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

using linear interpolation between these points, generated this lookup table
from speed to DMX value:

[
    (0.00479, 128),
    (0.005368888888888889, 129),
    (0.0059477777777777775, 130),
    (0.006526666666666667, 131),
    (0.007105555555555556, 132),
    (0.007684444444444444, 133),
    (0.008263333333333334, 134),
    (0.008842222222222222, 135),
    (0.009421111111111111, 136),
    (0.01, 137),
    (0.01069, 138),
    (0.01138, 139),
    (0.01207, 140),
    (0.01276, 141),
    (0.01345, 142),
    (0.01414, 143),
    (0.01483, 144),
    (0.015519999999999999, 145),
    (0.01621, 146),
    (0.0169, 147),
    (0.018209999999999997, 148),
    (0.01952, 149),
    (0.020829999999999998, 150),
    (0.02214, 151),
    (0.02345, 152),
    (0.024759999999999997, 153),
    (0.026069999999999996, 154),
    (0.027379999999999998, 155),
    (0.02869, 156),
    (0.03, 157),
    (0.03154, 158),
    (0.03308, 159),
    (0.03462, 160),
    (0.03616, 161),
    (0.0377, 162),
    (0.03924, 163),
    (0.040780000000000004, 164),
    (0.04232, 165),
    (0.04386, 166),
    (0.0454, 167),
    (0.04716, 168),
    (0.048920000000000005, 169),
    (0.05068, 170),
    (0.05244, 171),
    (0.0542, 172),
    (0.05596, 173),
    (0.05772, 174),
    (0.059480000000000005, 175),
    (0.06124, 176),
    (0.063, 177),
    (0.06462, 178),
    (0.06624000000000001, 179),
    (0.06786, 180),
    (0.06948, 181),
    (0.0711, 182),
    (0.07272, 183),
    (0.07434, 184),
    (0.07596, 185),
    (0.07758000000000001, 186),
    (0.0792, 187),
    (0.08188000000000001, 188),
    (0.08456000000000001, 189),
    (0.08724000000000001, 190),
    (0.08992, 191),
    (0.0926, 192),
    (0.09528, 193),
    (0.09796, 194),
    (0.10064000000000001, 195),
    (0.10332, 196),
    (0.106, 197),
    (0.10965, 198),
    (0.1133, 199),
    (0.11695, 200),
    (0.1206, 201),
    (0.12425, 202),
    (0.12789999999999999, 203),
    (0.13155, 204),
    (0.1352, 205),
    (0.13884999999999997, 206),
    (0.1425, 207),
    (0.14595, 208),
    (0.14939999999999998, 209),
    (0.15284999999999999, 210),
    (0.1563, 211),
    (0.15975, 212),
    (0.16319999999999998, 213),
    (0.16665, 214),
    (0.1701, 215),
    (0.17354999999999998, 216),
    (0.177, 217),
    (0.1835, 218),
    (0.19, 219),
    (0.1965, 220),
    (0.20299999999999999, 221),
    (0.2095, 222),
    (0.216, 223),
    (0.2225, 224),
    (0.22899999999999998, 225),
    (0.2355, 226),
    (0.242, 227),
    (0.2486, 228),
    (0.2552, 229),
    (0.2618, 230),
    (0.26839999999999997, 231),
    (0.275, 232),
    (0.28159999999999996, 233),
    (0.2882, 234),
    (0.2948, 235),
    (0.3014, 236),
    (0.308, 237),
    (0.3154, 238),
    (0.3228, 239),
    (0.3302, 240),
    (0.33759999999999996, 241),
    (0.345, 242),
    (0.35107142857142853, 243),
    (0.35714285714285715, 244),
    (0.3632142857142857, 245),
    (0.3692857142857143, 246),
    (0.37535714285714283, 247),
    (0.38142857142857145, 248),
    (0.3875, 249),
    (0.39458333333333334, 250),
    (0.40166666666666667, 251),
    (0.40875, 252),
    (0.41583333333333333, 253),
    (0.42291666666666666, 254),
    (0.43, 255),
]

--- Smart Move DMX ---

Some odd bucketing:
5 6 7 8 are the same speed
18 19 same speed

124 is slowest
133 is slowest in other direction
125-132 is stopped

251 250 249 248 same speed
238 237 same speed

Measurements:
[
    (255, 0.344),
    (249, 0.293),
    (245, 0.27),
    (235, 0.223),
    (225, 0.191),
    (215, 0.166),
    (205, 0.141),
    (195, 0.116),
    (193, 0.107),
    (191, 0.0972),
    (189, 0.0909),
    (187, 0.0794),
    (185, 0.0604),
    (184, 0.0481),
    (183, 0.0406),
    (181, 0.0306),
    (179, 0.0244),
    (176, 0.0194),
    (175, 0.0175),
    (165, 0.0102),
    (155, 0.00583),
    (145, 0.00270),
    (135, 0.00193),
]

This shit is bananas.

--- GOBO SPINNAZ ---

(DHA Varispeed driven by GOBO SPINNAZ driver)

Unsurprisingly, straight as an arrow, given linear voltage drive of a DC motor.
Max speed is MUCH slower than the other two rotator styles.

[
    (255, 0.185),
    (235, 0.170),
    (215, 0.156),
    (195, 0.141),
    (175, 0.127),
    (155, 0.111),
    (135, 0.0963),
    (115, 0.0825),
    (95, 0.0669),
    (75, 0.0523),
    (55, 0.0377),
    (35, 0.0225),
    (15, 0.0075),
]

If we normalize speed so the fastest rotator at max is 1, we lose a lot of the
upper range and resolution of the faster rotators.  I think I'll scale them so
that the slowest rotator's max speed is 1.0, but make the profiles understand
control signals outside of 1.0.

1.0 thus means 0.185 Hz or 11.1 rpm.
"""
from .param_gen import clamp

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
        speed = int(clamp(abs(value) * 255, 0, 255))
        return direction, speed

class RotoQDmx:
    """Control profile for Apollo Roto-Q DMX.

    Channel layout:
    0: direction/speed
    1: set to 0 for rotation mode
    """
    def __init__(self, address);
        self.address = address
        self.value = 0.0

    def render(self, buf):
        # 218 on the upper end is the speed for value = 1.0
        # 128 is the slowest in the positive direction
        # only about 90 real speed values otherwise in this range




def fill(r, x, s, ds_dx):
    values = []
    for value in r:
        base_s, base_x, base_ds_dx = s[0], x[0], ds_dx[0]
        for x0, s0, ds0 in zip(x, s, ds_dx):
            if value - x0 < 0:
                break
            base_s, base_x, base_ds_dx = s0, x0, ds0


        speed = base_s + (value - base_x)*base_ds_dx

        values.append((value, speed))
    return values




































