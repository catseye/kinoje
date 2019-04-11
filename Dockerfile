#
# docker build -t kinoje .
#
FROM python:3.5.7
WORKDIR /usr/src/app
COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt
COPY bin ./bin
COPY src ./src
