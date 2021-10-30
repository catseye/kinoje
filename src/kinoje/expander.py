from argparse import ArgumentParser
from copy import copy
import math
import os
import sys

from jinja2 import Template

from kinoje.utils import BaseProcessor, fmod, tween, load_config_file, items, zrange


class Expander(BaseProcessor):
    """Takes a directory and a template (Jinja2) and expands the template a number of times,
    creating a number of filled-out text files in the directory."""
    def __init__(self, config, dirname, **kwargs):
        super(Expander, self).__init__(config, **kwargs)
        self.dirname = dirname
        self.template = Template(config['template'])
        self.fun_context = {}
        for key, value in items(self.config.get('functions', {})):
            self.fun_context[key] = eval("lambda x: " + value)

    def fillout_template(self, frame, t):
        output_filename = os.path.join(self.dirname, "%08d.txt" % frame)
        if os.path.isfile(output_filename):
            return
        context = copy(self.config)
        context.update(self.fun_context)
        context.update({
            'width': float(self.config.get('width', 320.0)),
            'height': float(self.config.get('height', 200.0)),
            't': t,
            'math': math,
            'tween': tween,
            'fmod': fmod,
        })
        with open(output_filename, 'w') as f:
            f.write(self.template.render(context))

    def expand_all(self):
        t = self.config['start']
        t_step = self.config['t_step']
        for frame in self.tqdm(zrange(self.config['num_frames'])):
            self.fillout_template(frame, t)
            t += t_step


def main():
    argparser = ArgumentParser()

    argparser.add_argument('configfile', metavar='FILENAME', type=str,
        help='Configuration file containing the template and parameters'
    )
    argparser.add_argument('instantsdir', metavar='DIRNAME', type=str,
        help='Directory that will be populated with instants (text files describing frames)'
    )
    argparser.add_argument('--version', action='version', version="%(prog)s 0.8")

    options = argparser.parse_args(sys.argv[1:])

    config = load_config_file(options.configfile)

    expander = Expander(config, options.instantsdir)
    expander.expand_all()
