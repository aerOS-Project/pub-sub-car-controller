FROM python:3.10
WORKDIR /python-docker
COPY requirements.txt requirements.txt
RUN python3 -m pip install -r requirements.txt

COPY pubsub.py pubsub.py

ENV AEROS_CAR_DEMO_ORION_TOKEN=<YOUR-TOKEN-HERE>

EXPOSE 9098

CMD [ "python3", "pubsub.py", "urn:ngsi-ld:vehicle:5g-car:1", "--listen_port", "9098" ]