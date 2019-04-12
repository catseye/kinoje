#
# docker build -t kinoje .
# docker run --user $(id -u):$(id -g) -i -t -v "${PWD}:/usr/src/app/host" kinoje bin/kinoje host/eg/moebius.yaml -o host/moebius.mp4
#
FROM python:3.5.7-slim-stretch
RUN apt-get update && apt-get install -y povray povray-includes ffmpeg imagemagick
WORKDIR /usr/src/app
COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt
COPY bin ./bin
COPY src ./src
