from copy import copy
import math
import os

from kinoje.utils import fmod, tween


class Renderer(object):
    def __init__(self, dirname, template, config, fun_context, options, exe):
        self.dirname = dirname
        self.template = template
        self.config = config
        self.fun_context = fun_context
        self.options = options
        self.exe = exe

        render_type = config.get('type', 'povray')
        if render_type == 'povray':
            self.cmd_template = "povray -D +I{infile} +O{outfile} +W{width} +H{height} +A"
        elif render_type == 'svg':
            self.cmd_template = "inkscape -z -e {outfile} -w {width} -h {height} {infile}"
        else:
            raise NotImplementedError

    def render_frame(self, frame, t):
        out_pov = os.path.join(self.dirname, 'out.pov')
        context = copy(self.config)
        context.update(self.fun_context)
        context.update({
            'width': float(self.options.width),
            'height': float(self.options.height),
            't': t,
            'math': math,
            'tween': tween,
            'fmod': fmod,
        })
        with open(out_pov, 'w') as f:
            f.write(self.template.render(context))
        fn = os.path.join(self.dirname, self.options.frame_fmt % frame)
        cmd = self.cmd_template.format(
            infile=out_pov, outfile=fn, width=self.options.width, height=self.options.height
        )
        self.exe.do_it(cmd)
        return fn
