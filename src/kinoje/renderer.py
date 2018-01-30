from argparse import ArgumentParser
import re
import os
import sys

import yaml
try:
    from yaml import CLoader as Loader
except ImportError:
    from yaml import Loader

from kinoje.utils import LoggingExecutor


SUPPORTED_OUTPUT_FORMATS = ('.m4v', '.mp4', '.gif')


class Renderer(object):
    """Takes a source directory filled with text files and a destination directory and
    creates one image file in the destination directory from each text file in the source."""
    def __init__(self, command_template, src, dest, exe, width=320, height=200):
        self.command_template = command_template
        self.src = src
        self.dest = dest
        self.exe = exe
        self.width = width
        self.height = height

    def render_all(self):
        for filename in sorted(os.listdir(self.src)):
            full_srcname = os.path.join(self.src, filename)
            match = re.match(r'^.*?(\d+).*?$', filename)
            frame = int(match.group(1))
            destname = "%08d.png" % frame
            full_destname = os.path.join(self.dest, destname)
            self.render(frame, full_srcname, full_destname)

    def render(self, frame, full_srcname, full_destname):
        cmd = self.command_template.format(
            infile=full_srcname,
            indir=self.src,
            outfile=full_destname,
            width=self.width,
            height=self.height
        )
        self.exe.do_it(cmd)


def main():
    argparser = ArgumentParser()

    argparser.add_argument('configfile', metavar='FILENAME', type=str,
        help='Configuration file containing the template and parameters'
    )
    argparser.add_argument('instantsdir', metavar='DIRNAME', type=str,
        help='Directory containing instants (text file descriptions of each single frame) to render'
    )
    argparser.add_argument('framesdir', metavar='DIRNAME', type=str,
        help='Directory that will be populated with images, one for each frame'
    )

    options = argparser.parse_args(sys.argv[1:])

    with open(options.configfile, 'r') as file_:
        config = yaml.load(file_, Loader=Loader)

    exe = LoggingExecutor('movie.log')

    command_template = '???'
    renderer = Renderer(config['command_template'], options.instantsdir, options.framesdir, exe)
    renderer.render_all()

    exe.close()

    #run_duration = finished_at - started_at
    #print "Finished, took %s seconds" % run_duration.total_seconds()
