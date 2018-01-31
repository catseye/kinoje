kinoje
======

*Version 0.2.  Subject to backwards-incompatible changes without notice.*

**kinoje** is a templating-based animation tool.  A provided template is filled out once for each
frame of the animation; the result of the template expansion is used to create a still image; and
the resulting sequence of images is compiled into the finished movie.

Quick Start
-----------

The following are required:

*   **Python** 2.7 — to run the script
*   **PyYAML** and **Jinja2** — to fill out the templates
*   something to create images from filled-out templates — typically **POV-Ray** or **Inkscape**
*   **ffmpeg** or **ImageMagick** — to compile the images into a movie file

You might also find VLC useful, for viewing the final movie file.

On Ubuntu 16.04, you can install these with:

    pip install --user Jinja2 PyYAML
    sudo apt install povray povray-includes inkscape ffmpeg imagemagick vlc

You can then run the tool from the repository directory like so:

    bin/kinoje eg/moebius.yaml

Since no output filename was given, kinoje assumes MP4 format and automatically picks a reasonable
filename, in this case `moebius.mp4`.

You can also ask it to create a GIF by specifying an output filename with that as its file extension:

    bin/kinoje eg/squares.yaml -o squares.gif

File Format
-----------

The input YAML file must contain, at the minimum, a key called `template` giving a string (typically
a multi-line string) in Jinja2 syntax, which will be filled out once for each frame.

The context with which it will be filled out is constructed as follows:

*   `t` is a floating point value which will vary from 0.0 on the first frame to 1.0 on the last
    frame.  It is this value which will typically drive the animation.  For example, if the animation
    consists of moving a circle from x=0 to x=10, the part of the template which gives the x
    co-ordinate of the circle would be written as `{{ t * 10.0 }}`.
    
    And actually this is not 100% true.  `t` would be 1.0 on the frame after the last frame
    which, by definition, is never rendered.  On the last frame, it is 1.0 less a small value,
    which we could call the t-delta, and which varies based on the duration and the frame rate.

*   `math`, which is Python's math module, and which can be used to access functions such as `sin`.

*   `tween`, which is a function which is currently undocumented.

*   `fmod`, which is a function which is currently undocumented.

Other configuration options:

*   `duration` gives the duration, in seconds, to make the movie.  If omitted, it needs to be
    supplied on the command-line with the `--duration` option.

No further documentation on how to use the tool will be given, as it is all very subject to change
right now.
