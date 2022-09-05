from color_hustler import Application
use_rotos = True

if use_rotos:
    from color_hustler.gobo_rotator import SmartMoveDmx, RotoQDmx, GoboSpinna
    from color_hustler.dimmer import Dimmer
    import pyenttec

    rotos = [
        SmartMoveDmx(495),
        RotoQDmx(498),
        RotoQDmx(500),
        RotoQDmx(502),
        RotoQDmx(504),
        RotoQDmx(506),
        GoboSpinna(450),
        GoboSpinna(454),
    ]

    dimmers = [
        Dimmer(1),
        Dimmer(2),
        Dimmer(3),
        Dimmer(4),
    ]

    port = pyenttec.select_port()
else:
    rotos = []
    dimmers = []
    port = None


Application(dmx_port=port, rotos=rotos, dimmers=dimmers)