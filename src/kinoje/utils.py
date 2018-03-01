import os
import sys
from subprocess import check_call


def items(d):
    try:
        return d.iteritems()
    except AttributeError:
        return d.items()


def zrange(*args):
    try:
        return xrange(*args)
    except NameError:
        return range(*args)


def load_config_file(filename):
    import yaml
    try:
        from yaml import CLoader as Loader
    except ImportError:
        from yaml import Loader

    with open(filename, 'r') as file_:
        config = yaml.load(file_, Loader=Loader)

    config['libdir'] = os.path.dirname(filename)

    config['start'] = float(config.get('start', 0.0))
    config['stop'] = float(config.get('stop', 1.0))
    config['fps'] = float(config.get('fps', 25.0))
    config['width'] = float(config.get('width', 320.0))
    config['height'] = float(config.get('height', 200.0))

    duration = config['duration']
    start = config['start']
    stop = config['stop']
    fps = config['fps']

    config['start_time'] = start * duration
    config['stop_time'] = stop * duration
    config['requested_duration'] = config['stop_time'] - config['start_time']
    config['num_frames'] = int(config['requested_duration'] * fps)
    config['t_step'] = 1.0 / (duration * fps)

    return config


class LoggingExecutor(object):
    def __init__(self, filename):
        self.filename = filename
        self.log = open(filename, 'w')
        print("logging to {}".format(self.filename))

    def do_it(self, cmd, **kwargs):
        self.log.write('>>> {}\n'.format(cmd))
        self.log.flush()
        try:
            check_call(cmd, shell=True, stdout=self.log, stderr=self.log, **kwargs)
        except Exception as e:
            self.log.close()
            print(str(e))
            check_call("tail %s" % self.filename, shell=True)
            sys.exit(1)

    def close(self):
        self.log.close()


class Executor(object):
    def do_it(self, cmd, **kwargs):
        print(cmd)
        check_call(cmd, shell=True, **kwargs)

    def close(self):
        pass


def fmod(n, d):
    return n - d * int(n / d)


def tween(t, *args):
    """Format: after t, each arg should be like
        ((a, b), c)
    which means: when t >= a and < b, return c,
    or like
        ((a, b), (c, d))
    which means:
    when t >= a and < b, return a value between c and d which is proportional to the
    position between a and b that t is,
    or like
        ((a, b), (c, d), f)
    which means the same as case 2, except the function f is applied to the value between c and d
    before it is returned.
    """
    nargs = []
    for x in args:
        a = x[0]
        b = x[1]
        if not isinstance(x[1], tuple):
            b = (x[1], x[1])
        if len(x) == 2:
            f = lambda z: z
        else:
            f = x[2]
        nargs.append((a, b, f))

    for ((low, hi), (sc_low, sc_hi), f) in nargs:
        if t >= low and t < hi:
            pos = (t - low) / (hi - low)
            sc = sc_low + ((sc_hi - sc_low) * pos)
            return f(sc)
    raise ValueError(t)
