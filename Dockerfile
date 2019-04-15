FROM python:3.5.7-slim-stretch
RUN apt-get update && apt-get install -y povray povray-includes ffmpeg imagemagick librsvg2-bin
WORKDIR /usr/src/app
COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt
COPY bin ./bin
COPY src ./src
