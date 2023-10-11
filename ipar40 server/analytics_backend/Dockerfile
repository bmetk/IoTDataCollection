FROM python:3.10

ADD single_websocket.py /
ADD analytics.py /
ADD credentials.py /
ADD influx_write.py /
ADD sample_data_gen.py /
ADD requirements.txt /

RUN pip install -r requirements.txt

CMD [ "python", "./single_websocket.py" ]