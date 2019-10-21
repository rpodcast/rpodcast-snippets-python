# -*- Dockerfile -*-

FROM python:2.7.15-slim-jessie

# add libav-tools
RUN \
  echo "*** install pydub depedencies ***" && \
  apt-get update && \
  apt-get install -y libav-tools

# install python packages
RUN pip install paho-mqtt python-telegram-bot pyyaml pydub boto3

# establish conf volume and add python script
RUN mkdir -p /opt/tel2mqtt/conf
COPY telegram2mqtt.py /opt/tel2mqtt

# run the script
CMD ["python", "/opt/tel2mqtt/telegram2mqtt.py"]
