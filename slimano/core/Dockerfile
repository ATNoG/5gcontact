FROM python:3.7.3-stretch

COPY ./commons /sm_commons

WORKDIR /sm_commons

RUN pip install .

COPY ./core /slimano_core/

WORKDIR /slimano_core

VOLUME /slimano_core/configs

RUN pip install -r requirements.txt

CMD nameko run --config configs/config.yaml engine.engine
