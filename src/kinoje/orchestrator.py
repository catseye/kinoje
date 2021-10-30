from argparse import ArgumentParser
import os
import sys
from tempfile import mkdtemp, mkstemp

try:
    from tqdm import tqdm
except ImportError:
    def tqdm(x, **kwargs): return x

from kinoje.expander import Expander
from kinoje.renderer import Renderer
from kinoje.compiler import Compiler, SUPPORTED_OUTPUT_FORMATS

from kinoje.utils import LoggingExecutor, load_config_files


def main():
    argparser = ArgumentParser()

    argparser.add_argument('configfiles', metavar='FILENAME', type=str, nargs='+',
        help='A YAML file containing the template to render for each frame, '
             'as well as configuration for rendering the template. '
             'If multiple such configuration files are specified, successive '
             'files are applied as overlays.'
    )
    argparser.add_argument('-o', '--output', metavar='FILENAME', type=str, default=None,
        help='The movie file to create. The extension of this filename '
             'determines the output format and must be one of %r.  '
             'If not given, a default name will be chosen based on the '
             'configuration filename with a .mp4 extension added.' % (SUPPORTED_OUTPUT_FORMATS,)
    )
    argparser.add_argument('-d', '--work-dir', metavar='DIRNAME', type=str, default=None,
        help='The directory to store intermediate files in while creating '
             'this movie.  If not given, a directory will be created in '
             'the system temporary directory.'
    )
    argparser.add_argument('--version', action='version', version="%(prog)s 0.8")

    options, _unknown = argparser.parse_known_args(sys.argv[1:])

    if options.output is None:
        (configbase, configext) = os.path.splitext(os.path.basename(options.configfiles[0]))
        output_filename = configbase + '.mp4'
    else:
        output_filename = options.output

    CompilerClass = Compiler.get_class_for(output_filename)

    config = load_config_files(options.configfiles)

    if options.work_dir:
        work_dir = options.work_dir
        if not os.path.isdir(work_dir):
            os.mkdir(work_dir)
    else:
        work_dir =  mkdtemp()

    # TODO: append to this log if it already exists
    log_filename = os.path.join(work_dir, 'kinoje.log')
    exe = LoggingExecutor(log_filename)

    instants_dir = os.path.join(work_dir, 'instants')
    if not os.path.isdir(instants_dir):
        os.mkdir(instants_dir)

    frames_dir = os.path.join(work_dir, 'frames')
    if not os.path.isdir(frames_dir):
        os.mkdir(frames_dir)

    print('expanding template to instants in {}...'.format(instants_dir))
    expander = Expander(config, instants_dir, exe=exe, tqdm=tqdm)
    expander.expand_all()

    print('rendering instants to frames in {}...'.format(frames_dir))
    renderer = Renderer(config, instants_dir, frames_dir, exe=exe, tqdm=tqdm)
    renderer.render_all()

    print('compiling frames to movie file "{}"...'.format(output_filename))
    compiler = CompilerClass(config, frames_dir, output_filename, exe=exe, tqdm=tqdm)
    compiler.compile_all()

    exe.close()
