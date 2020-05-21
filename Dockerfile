FROM python:3.7

ADD . .
ADD .smartthings_cli.json /root/.smartthings_cli.json

RUN python setup.py install
