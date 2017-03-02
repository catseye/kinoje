kinoje
======

*Version 0.x, subject to change suddenly and erratically*

**kinoje** is a templating-based animation tool.  A provided template is filled out once for each
frame of the animation; the result of the template expansion is used to create a still image; and
the resulting sequence of images is compiled into the finished movie.

The following are required:

*   Python 2.7 — to run the script
*   PyYAML and Jinja2 — to fill out the templates
*   POV-Ray or Inkscape — to create the images from the filled-out templates
*   ffmpeg or ImageMagick — to compile the images into a movie file

You might also find VLC useful, for viewing the final movie file.

On Ubuntu 16.04, you can install these with:

    pip install --user Jinja2 PyYAML
    sudo apt install povray povray-includes inkscape ffmpeg imagemagick vlc

You can then run the tool from the repository directory like so:

    bin/kinoje eg/moebius.yaml moebius.mp4

You can also ask it to create a GIF by using that file extension:

    bin/kinoje eg/squares.yaml squares.gif --duration=2.0

No further documentation on how to use the tool will be given, as it is all very subject to change
right now.
