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
    (255, 0.43),
    (249, 0.3875),
    (242, 0.345),
    (237, 0.308),
    (227, 0.242),
    (217, 0.177),
    (207, 0.1425),
    (197, 0.106),
    (187, 0.0792),
    (177, 0.063),
    (167, 0.0454),
    (157, 0.030),
    (147, 0.0169),
    (137, 0.01),
    (128, 0.00479),
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

class RotoQDmx:
    pass