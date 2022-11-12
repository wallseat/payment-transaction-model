FROM python:3.10-slim

ENV PYTHONPATH=/app

COPY ./requirements.txt /tmp/requirements.txt

RUN pip install -r /tmp/requirements.txt

WORKDIR /app

COPY transaction/ /app/transaction/
