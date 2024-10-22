FROM python:3.12.7-alpine3.20 as base

FROM base as builder

RUN mkdir /install

WORKDIR /install

COPY requirements.txt /requirements.txt

RUN pip install --target /install -r /requirements.txt && \
    find /install -name '*.pyc' -delete && \
    find /install -name '__pycache__' -delete

FROM base

RUN apk update && apk upgrade

COPY --from=builder /install /usr/local

WORKDIR /app

COPY *.py /app/

RUN apk update && apk upgrade && \
    addgroup -S -g 10001 acme-user && adduser -S -u 10001 -G acme-user -H -s /sbin/nologin acme-user && \
    chown -R acme-user:acme-user /app && \
    apk del ca-certificates apk-tools && \
    rm -rf /usr/lib/python3.12/site-packages/pip* /usr/bin/pip*

USER acme-user

ENV PYTHONPATH=/usr/local

CMD ["python", "acme_challenge_dispatcher.py"]