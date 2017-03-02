"""\
kinoje {options} input-file.yaml output-file.{gif,m4v,mp4}

Create a movie file from the template and configuration in the given YAML file."""

# Note: just about everything here is subject to change!

from datetime import datetime, timedelta
from argparse import ArgumentParser
import os
import re
import sys
from tempfile import mkdtemp

from jinja2 import Template
import yaml
try:
    from yaml import CLoader as Loader
except ImportError:
    from yaml import Loader

from kinoje.utils import LoggingExecutor
from kinoje.renderer import Renderer
from kinoje.compiler import GifCompiler, MpegCompiler


SUPPORTED_OUTPUT_FORMATS = ('.m4v', '.mp4', '.gif')


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

    argparser.add_argument("--size", default=None, type=str,
        help=''
    )

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
    argparser.add_argument("--shorten-final-frame", default=False, action='store_true',
        help="Make the last frame in a GIF animation delay only half as long. "
             "Might make looping smoother when uploaded to Twitter. YMMV."
    )

    argparser.add_argument("--config", default=None, type=str)

    options = argparser.parse_args(sys.argv[1:])

    options.width, options.height = {
        'tiny': (160, 100),
        'small': (320, 200),
        'big': (640, 400),
        'huge': (800, 600),
        'giant': (1280, 800),
    }[options.size] if options.size is not None else (options.width, options.height)

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

    duration = options.duration
    if duration is None:
        duration = config['duration']

    start_time = options.start * duration
    stop_time = options.stop * duration
    requested_duration = stop_time - start_time
    num_frames = int(requested_duration * options.fps)
    t_step = 1.0 / (duration * options.fps)

    print "Start time: t=%s, %s seconds" % (options.start, start_time)
    print "Stop time: t=%s, %s seconds" % (options.stop, stop_time)
    print "Requested duration: %s seconds" % requested_duration
    print "Frame rate: %s fps" % options.fps
    print "Number of frames: %s (rounded to %s)" % (requested_duration * options.fps, num_frames)
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

        fn = renderer.render_frame(frame, t)

        t += t_step

        if options.still is not None:
            exe.do_it("eog %s" % fn)
            sys.exit(0)

    compiler = {
        '.gif': GifCompiler,
        '.mp4': MpegCompiler,
        '.m4v': MpegCompiler,
    }[outext](tempdir, outfilename, options, exe)

    compiler.compile(num_frames)
    finished_at = datetime.now()

    if options.view:
        compiler.view()

    exe.close()

    run_duration = finished_at - started_at
    print "Finished, took %s seconds" % run_duration.total_seconds()