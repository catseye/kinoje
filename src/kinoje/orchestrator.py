from datetime import datetime, timedelta
from argparse import ArgumentParser
import os
import re
import sys
from tempfile import mkdtemp, mkstemp

try:
    from tqdm import tqdm
except ImportError:
    def tqdm(x, **kwargs): return x

from kinoje.expander import Expander
from kinoje.renderer import Renderer
from kinoje.compiler import Compiler, SUPPORTED_OUTPUT_FORMATS

from kinoje.utils import LoggingExecutor, load_config_file


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

    CompilerClass = Compiler.get_class_for(output_filename)

    config = load_config_file(options.configfile)

    fd, log_filename = mkstemp()
    exe = LoggingExecutor(log_filename)

    instants_dir = mkdtemp()
    frames_dir = mkdtemp()

    print('expanding template to instants...')
    expander = Expander(config, instants_dir, exe=exe, tqdm=tqdm)
    expander.expand_all()

    print('rendering instants to frames...')
    renderer = Renderer(config, instants_dir, frames_dir, exe=exe, tqdm=tqdm)
    renderer.render_all()

    print('compiling frames to movie...')
    compiler = CompilerClass(config, frames_dir, output_filename, exe=exe, tqdm=tqdm)
    compiler.compile_all()

    exe.close()
    os.close(fd)
