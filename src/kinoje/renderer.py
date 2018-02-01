from argparse import ArgumentParser
import re
import os
import sys

import yaml
try:
    from yaml import CLoader as Loader
except ImportError:
    from yaml import Loader

from kinoje.utils import LoggingExecutor, load_config_file


class Renderer(object):
    """Takes a source directory filled with text files and a destination directory and
    creates one image file in the destination directory from each text file in the source."""
    def __init__(self, config, src, dest, exe):
        self.command = config['command']
        self.libdir = config['libdir']
        self.src = src
        self.dest = dest
        self.exe = exe
        self.width = config['width']
        self.height = config['height']

    def render_all(self):
        for filename in sorted(os.listdir(self.src)):
            full_srcname = os.path.join(self.src, filename)
            match = re.match(r'^.*?(\d+).*?$', filename)
            frame = int(match.group(1))
            destname = "%08d.png" % frame
            full_destname = os.path.join(self.dest, destname)
            self.render(frame, full_srcname, full_destname)

    def render(self, frame, full_srcname, full_destname):
        cmd = self.command.format(
            infile=full_srcname,
            libdir=self.libdir,
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

    config = load_config_file(options.configfile)

    exe = LoggingExecutor('renderer.log')

    renderer = Renderer(config, options.instantsdir, options.framesdir, exe)
    renderer.render_all()

    exe.close()
