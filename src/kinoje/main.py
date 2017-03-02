"""\
kinoje {options} input-file.yaml output-file.{gif,m4v,mp4}

Create a movie file from the template and configuration in the given YAML file."""

# Note: just about everything here is subject to change!

from datetime import datetime, timedelta
from copy import copy
import math
from optparse import OptionParser
import os
import re
from subprocess import check_call
import sys
from tempfile import mkdtemp

from jinja2 import Template
import yaml
try:
    from yaml import CLoader as Loader
except ImportError:
    from yaml import Loader


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


def main():
    optparser = OptionParser(__doc__)
    optparser.add_option("--width", default=320, type=int)
    optparser.add_option("--height", default=200, type=int)

    optparser.add_option("--tiny", default=False, action='store_true')
    optparser.add_option("--small", default=False, action='store_true')
    optparser.add_option("--big", default=False, action='store_true')
    optparser.add_option("--huge", default=False, action='store_true')
    optparser.add_option("--giant", default=False, action='store_true')
    optparser.add_option("--square", default=False, action='store_true')

    optparser.add_option("--start", default=0.0, type=float, metavar='INSTANT',
        help="t-value at which to start rendering the movie.  Default=0.0"
    )
    optparser.add_option("--stop", default=1.0, type=float, metavar='INSTANT',
        help="t-value at which to stop rendering the movie.  Default=1.0"
    )
    optparser.add_option("--duration", default=None, type=float, metavar='SECONDS',
        help="Override the duration specified in the configuration."
    )

    optparser.add_option("--fps", default=25.0, type=float, metavar='FPS',
        help="The number of frames to render for each second.  Note that the "
             "tool that makes a movie file from images might not honour this value exactly."
    )
    optparser.add_option("--still", default=None, type=float)
    optparser.add_option("--view", default=False, action='store_true')
    optparser.add_option("--twitter", default=False, action='store_true',
        help="Make the last frame in a GIF animation delay only half as long."
    )

    optparser.add_option("--config", default=None, type=str)

    (options, args) = optparser.parse_args(sys.argv[1:])

    if options.tiny:
        options.width = 160
        options.height = 100
    if options.small:
        options.width = 320
        options.height = 200
    if options.big:
        options.width = 640
        options.height = 400
    if options.huge:
        options.width = 800
        options.height = 600
    if options.giant:
        options.width = 1280
        options.height = 800

    if options.square:
        options.height = options.width

    if options.still is not None:
        options.duration = 1.0
        options.start = options.still

    infilename = args[0]
    try:
        outfilename = args[1]
    except IndexError:
        (inbase, inext) = os.path.splitext(infilename)
        outfilename = inbase + '.mp4'
    (whatever, outext) = os.path.splitext(outfilename)
    SUPPORTED_OUTPUT_FORMATS = ('.m4v', '.mp4', '.gif')
    if outext not in SUPPORTED_OUTPUT_FORMATS:
        raise ValueError("%s not a supported output format (%r)" % (outext, SUPPORTED_OUTPUT_FORMATS))

    with open(infilename, 'r') as file_:
        config = yaml.load(file_, Loader=Loader)

    if options.config is not None:
        settings = {}
        for setting_string in options.config.split(','):
            key, value = setting_string.split(':')
            if re.match(r'^\d*\.?\d*$', value):
                value = float(value)
            settings[key] = value
        config.update(settings)

    template = Template(config['template'])

    fun_context = {}
    for key, value in config.get('functions', {}).iteritems():
        fun_context[key] = eval("lambda x: " + value)

    tempdir = mkdtemp()

    frame_fmt = "out%05d.png"
    framerate = options.fps

    duration = options.duration
    if duration is None:
        duration = config['duration']

    start_time = options.start * duration
    stop_time = options.stop * duration
    requested_duration = stop_time - start_time
    num_frames = int(requested_duration * framerate)
    t_step = 1.0 / (duration * framerate)

    print "Start time: t=%s, %s seconds" % (options.start, start_time)
    print "Stop time: t=%s, %s seconds" % (options.stop, stop_time)
    print "Requested duration: %s seconds" % requested_duration
    print "Frame rate: %s fps" % framerate
    print "Number of frames: %s (rounded to %s)" % (requested_duration * framerate, num_frames)
    print "t-Step: %s" % t_step

    exe = LoggingExecutor(os.path.join(tempdir, 'movie.log'))
    t = options.start

    started_at = datetime.now()

    for frame in xrange(num_frames):

        elapsed = (datetime.now() - started_at).total_seconds()
        eta = '???'
        if frame > 0:
            seconds_per_frame = elapsed / float(frame)
            eta = started_at + timedelta(seconds=num_frames * seconds_per_frame)

        print "t=%s (%s%% done, eta %s)" % (t, int(((t - options.start) / options.stop) * 100), eta)

        out_pov = os.path.join(tempdir, 'out.pov')
        context = copy(config)
        context.update(fun_context)
        context.update({
            'width': float(options.width),
            'height': float(options.height),
            't': t,
            'math': math,
            'tween': tween,
            'fmod': fmod,
        })
        with open(out_pov, 'w') as f:
            f.write(template.render(context))
        fn = os.path.join(tempdir, frame_fmt % frame)
        render_type = config.get('type', 'povray')
        if render_type == 'povray':
            cmd_template = "povray -D +I{infile} +O{outfile} +W{width} +H{height} +A"
        elif render_type == 'svg':
            cmd_template = "inkscape -z -e {outfile} -w {width} -h {height} {infile}"
        else:
            raise NotImplementedError
        cmd = cmd_template.format(
            infile=out_pov, outfile=fn, width=options.width, height=options.height
        )
        exe.do_it(cmd)
        t += t_step

        if options.still is not None:
            exe.do_it("eog %s" % fn)
            sys.exit(0)

    if outext == '.gif':
        # TODO: show some warning if this is not an integer delay
        delay = int(100.0 / framerate)

        filenames = [os.path.join(tempdir, frame_fmt % f) for f in xrange(0, num_frames)]
        if options.twitter:
            filespec = ' '.join(filenames[:-1] + ['-delay', str(delay / 2), filenames[-1]])
        else:
            filespec = ' '.join(filenames)

        # -strip is there to force convert to process all input files.  (if no transformation is given,
        # it can sometimes stop reading input files.  leading to skippy animations.  who knows why.)
        exe.do_it("convert -delay %s -loop 0 %s -strip %s" % (
            delay, filespec, outfilename
        ))
        finished_at = datetime.now()
        if options.view:
            exe.do_it("eog %s" % outfilename)
    elif outext in ('.mp4', '.m4v'):
        ifmt = os.path.join(tempdir, frame_fmt)
        # fun fact: even if you say -r 30, it still picks 25 fps
        cmd = "ffmpeg -i %s -c:v libx264 -profile:v baseline -pix_fmt yuv420p -r %s -y %s" % (
            ifmt, int(framerate), outfilename
        )
        exe.do_it(cmd)
        finished_at = datetime.now()
        if options.view:
            exe.do_it("vlc %s" % outfilename)
    else:
        raise NotImplementedError

    exe.close()

    run_duration = finished_at - started_at
    print "Finished, took %s seconds" % run_duration.total_seconds()
