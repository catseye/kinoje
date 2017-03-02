import os


class Compiler(object):
    def __init__(self, dirname, outfilename, options, exe):
        self.dirname = dirname
        self.options = options
        self.exe = exe
        self.outfilename = outfilename


class GifCompiler(Compiler):
    
    def compile(self, num_frames):
        # TODO: show some warning if this is not an integer delay
        delay = int(100.0 / self.options.fps)

        filenames = [os.path.join(self.dirname, self.options.frame_fmt % f) for f in xrange(0, num_frames)]
        if self.options.shorten_final_frame:
            filespec = ' '.join(filenames[:-1] + ['-delay', str(delay / 2), filenames[-1]])
        else:
            filespec = ' '.join(filenames)

        # -strip is there to force convert to process all input files.  (if no transformation is given,
        # it can sometimes stop reading input files.  leading to skippy animations.  who knows why.)
        self.exe.do_it("convert -delay %s -loop 0 %s -strip %s" % (
            delay, filespec, self.outfilename
        ))

    def view(self):
        self.exe.do_it("eog %s" % self.outfilename)


class MpegCompiler(Compiler):

    def compile(self, num_frames):
        ifmt = os.path.join(self.dirname, self.options.frame_fmt)
        # fun fact: even if you say -r 30, ffmpeg still picks 25 fps
        cmd = "ffmpeg -i %s -c:v libx264 -profile:v baseline -pix_fmt yuv420p -r %s -y %s" % (
            ifmt, int(self.options.fps), self.outfilename
        )
        self.exe.do_it(cmd)

    def view(self):
        self.exe.do_it("vlc %s" % self.outfilename)
