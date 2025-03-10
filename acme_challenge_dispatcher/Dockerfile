FROM python:3.12.9-alpine3.21

RUN apk add --no-cache --update && apk upgrade --no-cache && rm -rf /var/cache/apk/*

COPY requirements.txt /requirements.txt
RUN --mount=type=cache,target=/root/.cache/pip pip install --root-user-action=ignore -r /requirements.txt

WORKDIR /app

COPY log_functions.py k8s_functions.py acme_challenge_dispatcher.py /app/

RUN python -m pip uninstall --root-user-action=ignore -y pip && \
    apk --purge del apk-tools && \
    rm -rf ~/.cache

RUN addgroup -S -g 10001 acme-user \
    && adduser -S -u 10001 -G acme-user -H -s /sbin/nologin acme-user \
    && chown -R acme-user:acme-user /app

USER acme-user

CMD ["python", "acme_challenge_dispatcher.py"]