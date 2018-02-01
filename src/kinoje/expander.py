from argparse import ArgumentParser
from copy import copy
import math
import os
import sys

from jinja2 import Template

from kinoje.utils import LoggingExecutor, fmod, tween, load_config_file


class Expander(object):
    """Takes a directory and a template (Jinja2) and expands the template a number of times,
    creating a number of filled-out text files in the directory."""
    def __init__(self, dirname, template, config, exe):
        self.dirname = dirname
        self.template = template
        self.config = config
        self.exe = exe

        self.fun_context = {}
        for key, value in self.config.get('functions', {}).iteritems():
            self.fun_context[key] = eval("lambda x: " + value)

    def fillout_template(self, frame, t):
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
        output_filename = os.path.join(self.dirname, "%08d.txt" % frame)
        with open(output_filename, 'w') as f:
            f.write(self.template.render(context))


def main():
    argparser = ArgumentParser()

    argparser.add_argument('configfile', metavar='FILENAME', type=str,
        help='Configuration file containing the template and parameters'
    )
    argparser.add_argument('instantsdir', metavar='DIRNAME', type=str,
        help='Directory that will be populated with instants (text files describing frames)'
    )

    options = argparser.parse_args(sys.argv[1:])

    config = load_config_file(options.configfile)
    template = Template(config['template'])

    exe = LoggingExecutor('movie.log')

    expander = Expander(options.instantsdir, template, config, exe)

    t = config['start']
    t_step = config['t_step']
    for frame in xrange(config['num_frames']):
        expander.fillout_template(frame, t)
        t += t_step

    exe.close()
