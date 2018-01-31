from datetime import datetime, timedelta
from argparse import ArgumentParser
import os
import re
import sys
from tempfile import mkdtemp

from kinoje.utils import Executor, load_config_file


SUPPORTED_OUTPUT_FORMATS = ('.m4v', '.mp4', '.gif')


def main():
    argparser = ArgumentParser()

    argparser.add_argument('configfile', metavar='FILENAME', type=str,
        help='A YAML file containing the template to render for each frame, '
             'as well as configuration for rendering the template.'
    )
    argparser.add_argument('output', metavar='FILENAME', type=str,
        help='The movie file to create. The extension of this filename '
             'determines the output format and must be one of %r.  '
             'If not given, a default name will be chosen based on the '
             'configuration filename with a .mp4 extension added.' % (SUPPORTED_OUTPUT_FORMATS,)
    )

    options, unknown = argparser.parse_known_args(sys.argv[1:])
    remainder = ' '.join(unknown)

    exe = Executor()

    instants_dir = mkdtemp()
    frames_dir = mkdtemp()

    exe.do_it("kinoje-expand {} {}".format(options.configfile, instants_dir))
    exe.do_it("kinoje-render {} {} {}".format(options.configfile, instants_dir, frames_dir))
    exe.do_it("kinoje-compile {} {} {} {}".format(options.configfile, frames_dir, options.output, remainder))

    exe.close()
