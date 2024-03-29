from argparse import ArgumentParser
import os
import sys

from kinoje.utils import BaseProcessor, load_config_file, zrange


SUPPORTED_OUTPUT_FORMATS = ('.m4v', '.mp4', '.gif')


class Compiler(BaseProcessor):
    def __init__(self, config, dirname, outfilename, **kwargs):
        super(Compiler, self).__init__(config, **kwargs)
        self.dirname = dirname
        self.outfilename = outfilename
        self.frame_fmt = "%08d.png"

    @classmethod
    def get_class_for(cls, filename):
        (whatever, outext) = os.path.splitext(filename)
        if outext not in SUPPORTED_OUTPUT_FORMATS:
            raise ValueError("%s not a supported output format (%r)" % (outext, SUPPORTED_OUTPUT_FORMATS))
        return {
            '.gif': GifCompiler,
            '.mp4': MpegCompiler,
            '.m4v': MpegCompiler,
        }[outext]

    def compile(self, num_frames):
        raise NotImplementedError

    def compile_all(self):
        tasks = [lambda: self.compile(self.config['num_frames'])]
        for task in self.tqdm(tasks):
            result = task()
        return result


class GifCompiler(Compiler):
    
    def compile(self, num_frames):
        # TODO: show some warning if this is not an integer delay
        delay = int(100.0 / self.config['fps'])

        filenames = [os.path.join(self.dirname, self.frame_fmt % f) for f in zrange(0, num_frames)]
        if self.config.get('shorten_final_frame'):
            filespec = ' '.join(filenames[:-1] + ['-delay', str(delay / 2), filenames[-1]])
        else:
            filespec = ' '.join(filenames)

        # -strip is there to force convert to process all input files.  (if no transformation is given,
        # it can sometimes stop reading input files.  leading to skippy animations.  who knows why.)
        self.exe.do_it(
            ["convert", "-delay", delay, "-loop", "0", filespec, "-strip", self.outfilename],
            shell=False
        )

    def view(self):
        self.exe.do_it(["eog", self.outfilename], shell=False)


class MpegCompiler(Compiler):

    def compile(self, num_frames):
        ifmt = os.path.join(self.dirname, self.frame_fmt)
        # fun fact: even if you say -r 30, ffmpeg still picks 25 fps
        self.exe.do_it(
            ["ffmpeg", "-i", ifmt, "-c:v", "libx264", "-profile:v", "baseline", "-pix_fmt", "yuv420p",
             "-r", str(int(self.config['fps'])), "-y", self.outfilename],
            shell=False
        )

    def view(self):
        self.exe.do_it(["vlc", self.outfilename], shell=False)


def main():
    argparser = ArgumentParser()

    argparser.add_argument('configfile', metavar='FILENAME', type=str,
        help='Configuration file containing the template and parameters'
    )
    argparser.add_argument('framesdir', metavar='DIRNAME', type=str,
        help='Directory that will be populated with image of each single frame'
    )
    argparser.add_argument('output', metavar='FILENAME', type=str,
        help='The movie file to create. The extension of this filename '
             'determines the output format and must be one of %r.  '
             'If not given, a default name will be chosen based on the '
             'configuration filename with a .mp4 extension added.' % (SUPPORTED_OUTPUT_FORMATS,)
    )

    argparser.add_argument("--shorten-final-frame", default=False, action='store_true',
        help="Make the last frame in a GIF animation delay only half as long. "
             "Might make looping smoother when uploaded to Twitter. YMMV."
    )
    argparser.add_argument("--view", default=False, action='store_true',
        help="Display the resultant movie."
    )
    argparser.add_argument('--version', action='version', version="%(prog)s 0.8")

    options = argparser.parse_args(sys.argv[1:])

    (whatever, outext) = os.path.splitext(options.output)
    if outext not in SUPPORTED_OUTPUT_FORMATS:
        raise ValueError("%s not a supported output format (%r)" % (outext, SUPPORTED_OUTPUT_FORMATS))

    config = load_config_file(options.configfile)
    config['shorten_final_frame'] = options.shorten_final_frame

    compiler = Compiler.get_class_for(options.output)(config, options.framesdir, options.output)
    compiler.compile_all()

    if options.view:
        compiler.view()
