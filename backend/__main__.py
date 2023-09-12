from color_hustler import Application
use_rotos = True

if use_rotos:
    from color_hustler.gobo_rotator import SmartMoveDmx, RotoQDmx, GoboSpinna, Varispeed
    from color_hustler.dimmer import Dimmer
    import pyenttec

    rotos = [
        SmartMoveDmx(495),
        RotoQDmx(498),
        RotoQDmx(500),
        RotoQDmx(502),
        RotoQDmx(504),
        RotoQDmx(506),
        GoboSpinna(470),
        GoboSpinna(474),
        Varispeed(1),
        Varispeed(5),
    ]

    dimmers = [Dimmer(x+460) for x in range(0, 8)]
    print(len(dimmers))

    port = pyenttec.select_port()
else:
    rotos = []
    dimmers = []
    port = None


Application(dmx_port=port, rotos=rotos, dimmers=dimmers)
