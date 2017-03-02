"""\
kinoje {options} input-file.yaml output-file.{gif,m4v,mp4}

Create a movie file from the template and configuration in the given YAML file."""

# Note: just about everything here is subject to change!

from datetime import datetime, timedelta
from copy import copy
import math
from argparse import ArgumentParser
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


SUPPORTED_OUTPUT_FORMATS = ('.m4v', '.mp4', '.gif')


### helpers ###


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


### renderer ###


class Renderer(object):
    def __init__(self, dirname, template, config, fun_context, options, exe):
        self.dirname = dirname
        self.template = template
        self.config = config
        self.fun_context = fun_context
        self.options = options
        self.exe = exe

        render_type = config.get('type', 'povray')
        if render_type == 'povray':
            self.cmd_template = "povray -D +I{infile} +O{outfile} +W{width} +H{height} +A"
        elif render_type == 'svg':
            self.cmd_template = "inkscape -z -e {outfile} -w {width} -h {height} {infile}"
        else:
            raise NotImplementedError

    def render_frame(self, frame, t):
        out_pov = os.path.join(self.dirname, 'out.pov')
        context = copy(self.config)
        context.update(self.fun_context)
        context.update({
            'width': float(self.options.width),
            'height': float(self.options.height),
            't': t,
            'math': math,
            'tween': tween,
            'fmod': fmod,
        })
        with open(out_pov, 'w') as f:
            f.write(self.template.render(context))
        fn = os.path.join(self.dirname, self.options.frame_fmt % frame)
        cmd = self.cmd_template.format(
            infile=out_pov, outfile=fn, width=self.options.width, height=self.options.height
        )
        self.exe.do_it(cmd)


### main ###


def main():
    argparser = ArgumentParser()
    
    argparser.add_argument('configfile', metavar='FILENAME', type=str,
        help='A YAML file containing the template to render for each frame, '
             'as well as configuration for rendering the template.'
    )
    argparser.add_argument('-o', '--output', metavar='FILENAME', type=str, default=None,
        help='The movie file to create. The extension of this filename '
             'determines the output format and must be one of %r.  '
             'If not given, a default name will be chosen based on the '
             'configuration filename with a .mp4 extension added.' % (SUPPORTED_OUTPUT_FORMATS,)
    )

    argparser.add_argument("--width", default=320, type=int)
    argparser.add_argument("--height", default=200, type=int)

    argparser.add_argument("--tiny", default=False, action='store_true')
    argparser.add_argument("--small", default=False, action='store_true')
    argparser.add_argument("--big", default=False, action='store_true')
    argparser.add_argument("--huge", default=False, action='store_true')
    argparser.add_argument("--giant", default=False, action='store_true')
    argparser.add_argument("--square", default=False, action='store_true')

    argparser.add_argument("--start", default=0.0, type=float, metavar='INSTANT',
        help="t-value at which to start rendering the movie.  Default=0.0"
    )
    argparser.add_argument("--stop", default=1.0, type=float, metavar='INSTANT',
        help="t-value at which to stop rendering the movie.  Default=1.0"
    )
    argparser.add_argument("--duration", default=None, type=float, metavar='SECONDS',
        help="Override the duration specified in the configuration."
    )

    argparser.add_argument("--fps", default=25.0, type=float, metavar='FPS',
        help="The number of frames to render for each second.  Note that the "
             "tool that makes a movie file from images might not honour this value exactly."
    )
    argparser.add_argument("--frame-fmt", default="out%05d.png", type=str)

    argparser.add_argument("--still", default=None, type=float, metavar='INSTANT',
        help="If given, generate only a single frame (at the specified instant "
             "betwen 0.0 and 1.0) and display it using eog, instead of building "
             "the whole movie."
    )
    argparser.add_argument("--view", default=False, action='store_true')
    argparser.add_argument("--twitter", default=False, action='store_true',
        help="Make the last frame in a GIF animation delay only half as long."
    )

    argparser.add_argument("--config", default=None, type=str)

    options = argparser.parse_args(sys.argv[1:])

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

    infilename = options.configfile
    outfilename = options.output
    if options.output is None:
        (inbase, inext) = os.path.splitext(os.path.basename(infilename))
        outfilename = inbase + '.mp4'
    (whatever, outext) = os.path.splitext(outfilename)
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

    renderer = Renderer(tempdir, template, config, fun_context, options, exe)

    for frame in xrange(num_frames):

        elapsed = (datetime.now() - started_at).total_seconds()
        eta = '???'
        if frame > 0:
            seconds_per_frame = elapsed / float(frame)
            eta = started_at + timedelta(seconds=num_frames * seconds_per_frame)

        print "t=%s (%s%% done, eta %s)" % (t, int(((t - options.start) / options.stop) * 100), eta)

        renderer.render_frame(frame, t)

        t += t_step

        if options.still is not None:
            exe.do_it("eog %s" % fn)
            sys.exit(0)

    if outext == '.gif':
        # TODO: show some warning if this is not an integer delay
        delay = int(100.0 / framerate)

        filenames = [os.path.join(tempdir, options.frame_fmt % f) for f in xrange(0, num_frames)]
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
        ifmt = os.path.join(tempdir, options.frame_fmt)
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
