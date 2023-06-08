FROM eclipse-mosquitto:2.0.15

COPY ./entrypoint.sh /
RUN chmod +x /entrypoint.sh

RUN echo "starting entrypoint"
ENTRYPOINT ["/entrypoint.sh"]

CMD ["/usr/sbin/mosquitto","-c","/mosquitto/config/mosquitto.conf"]