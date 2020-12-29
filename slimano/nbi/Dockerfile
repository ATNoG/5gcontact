FROM python:3.7.3-stretch

COPY ./commons /sm_commons

WORKDIR /sm_commons

RUN pip install .

COPY ./nbi /slimano_nbi/

WORKDIR /slimano_nbi

VOLUME /slimano_nbi/configs

RUN pip install -r requirements.txt

CMD python main.py configs/config.ini
# CMD tail -F /dev/null
