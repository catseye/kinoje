from argparse import ArgumentParser
import re
import os
import sys

from kinoje.utils import BaseProcessor, load_config_file


class Renderer(BaseProcessor):
    """Takes a source directory filled with text files and a destination directory and
    creates one image file in the destination directory from each text file in the source."""
    def __init__(self, config, src, dest, **kwargs):
        super(Renderer, self).__init__(config, **kwargs)
        self.src = src
        self.dest = dest
        self.command = config['command']
        self.libdir = config['libdir']
        self.width = config['width']
        self.height = config['height']

    def render_all(self):
        for filename in self.tqdm(sorted(os.listdir(self.src))):
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
            width=int(self.width),
            height=int(self.height),
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
    argparser.add_argument('--version', action='version', version="%(prog)s 0.7")

    options = argparser.parse_args(sys.argv[1:])

    config = load_config_file(options.configfile)

    renderer = Renderer(config, options.instantsdir, options.framesdir)
    renderer.render_all()
