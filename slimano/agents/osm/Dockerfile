FROM python:3.6.8-stretch

COPY ./commons /sm_commons

WORKDIR /sm_commons

RUN pip install .

COPY ./agents/osm /sm_osm_agent/

WORKDIR /sm_osm_agent

VOLUME /sm_osm_agent/configs

RUN pip install -r requirements.txt

CMD nameko run --config configs/config.yaml osm_agent