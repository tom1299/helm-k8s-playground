FROM python:3.12-slim

WORKDIR /app

RUN useradd -m -s /bin/sh behave

USER behave

ENV PATH="/home/behave/.local/bin:${PATH}"

COPY requirements.txt requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

COPY features features

ENTRYPOINT ["behave", "/app/features"]