FROM python:3.12.7-alpine3.20

RUN apk update && apk upgrade

COPY requirements.txt /requirements.txt
RUN pip install -r /requirements.txt

RUN mkdir /app
WORKDIR /app
COPY *.py /app/

RUN addgroup -S -g 10001 acme-user
RUN adduser -S -u 10001 -G acme-user -H -s /sbin/nologin acme-user
RUN chown -R acme-user:acme-user /app

USER acme-user

CMD ["python", "acme_challenge_dispatcher.py"]