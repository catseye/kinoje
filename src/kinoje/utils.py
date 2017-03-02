import sys
from subprocess import check_call


class LoggingExecutor(object):
    def __init__(self, filename):
        self.filename = filename
        self.log = open(filename, 'w')

    def do_it(self, cmd, **kwargs):
        print cmd
        try:
            check_call(cmd, shell=True, stdout=self.log, stderr=self.log, **kwargs)
        except Exception as e:
            self.log.close()
            print str(e)
            check_call("tail %s" % self.filename, shell=True)
            sys.exit(1)

    def close(self):
        self.log.close()


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
