from color_hustler import Application
use_rotos = True

if use_rotos:
    from color_hustler.gobo_rotator import SmartMoveDmx, RotoQDmx, GoboSpinna
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

    port = pyenttec.select_port()
else:
    rotos = []
    port = None


Application(dmx_port=port, rotos=rotos)