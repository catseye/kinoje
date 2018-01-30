"""\
kinoje {options} input-file.yaml output-dir/

Create a sequence of text file descriptions of frames of a movie from the
configuration (which incl. a master template) in the given YAML file."""

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


def main():
    argparser = ArgumentParser()

    argparser.add_argument('configfile', metavar='FILENAME', type=str,
        help='A YAML file containing the template to render for each frame, '
             'as well as configuration for rendering the template.'
    )

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

    text_files_dir = mkdtemp()
    images_dir = mkdtemp()

    duration = options.duration
    if duration is None:
        duration = config['duration']

    if 'render_command_template' not in config:
        render_type = config.get('type', 'povray')
        if render_type == 'povray':
            config['render_command_template'] = "povray +L{indir} -D +I{infile} +O{outfile} +W{width} +H{height} +A"
        elif render_type == 'svg':
            config['render_command_template'] = "inkscape -z -e {outfile} -w {width} -h {height} {infile}"
        else:
            raise NotImplementedError

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

    exe = LoggingExecutor(os.path.join(text_files_dir, 'movie.log'))
    t = options.start

    started_at = datetime.now()

    expander = TemplateExpander(text_files_dir, template, config, options, exe)
    for frame in xrange(num_frames):
        expander.fillout_template(frame, t)
        t += t_step

    exe.close()

    run_duration = finished_at - started_at
    print "Finished, took %s seconds" % run_duration.total_seconds()
