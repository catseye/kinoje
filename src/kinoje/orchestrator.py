from datetime import datetime, timedelta
from argparse import ArgumentParser
import os
import re
import sys
from tempfile import mkdtemp

from kinoje.expander import Expander
from kinoje.renderer import Renderer
from kinoje.compiler import Compiler

from kinoje.utils import Executor, load_config_file


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

    options, unknown = argparser.parse_known_args(sys.argv[1:])
    remainder = ' '.join(unknown)

    if options.output is None:
        (configbase, configext) = os.path.splitext(os.path.basename(options.configfile))
        output_filename = configbase + '.mp4'
    else:
        output_filename = options.output
    (whatever, outext) = os.path.splitext(output_filename)
    if outext not in SUPPORTED_OUTPUT_FORMATS:
        raise ValueError("%s not a supported output format (%r)" % (outext, SUPPORTED_OUTPUT_FORMATS))

    config = load_config_file(options.configfile)

    exe = Executor()

    instants_dir = mkdtemp()
    frames_dir = mkdtemp()

    expander = Expander(config, instants_dir, exe=exe)
    expander.expand_all()

    renderer = Renderer(config, instants_dir, frames_dir, exe=exe)
    renderer.render_all()

    compiler = Compiler.get_class_for(output_filename)(config, frames_dir, output_filename, exe=exe)
    compiler.compile_all()

    exe.close()
