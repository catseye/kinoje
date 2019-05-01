#!/bin/sh

# After building the image, you can run kinoje from within it like:
#
# docker run --user $(id -u):$(id -g) -i -t -v "${PWD}:/mnt/host" kinoje \
#        kinoje eg/moebius.yaml -o moebius.mp4
#

rm -rf src/kinoje/*.pyc src/kinoje/__pycache__
docker container prune
docker rmi catseye/kinoje:0.6
docker rmi kinoje
docker build -t kinoje .
docker tag kinoje catseye/kinoje:0.6
