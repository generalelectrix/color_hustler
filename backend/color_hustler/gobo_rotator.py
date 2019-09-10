"""Fixture driver for various gobo rotators.

Reverse-engineered profiles:
Roto-Q DMX:
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

Some measurements:
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
"""

class RotoQDmx:
    pass