from copy import copy
import math
import os

from kinoje.utils import fmod, tween


class Renderer(object):
    def __init__(self, dirname, template, config, options, exe):
        self.dirname = dirname
        self.template = template
        self.config = config
        self.options = options
        self.exe = exe

        self.fun_context = {}
        for key, value in self.config.get('functions', {}).iteritems():
            self.fun_context[key] = eval("lambda x: " + value)

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
        cmd = self.config['render_command_template'].format(
            infile=out_pov, outfile=fn, width=self.options.width, height=self.options.height
        )
        self.exe.do_it(cmd)
        return fn
