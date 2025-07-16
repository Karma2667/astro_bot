FROM python:3.12

RUN mkdir /astro_bot

WORKDIR /astro_bot

COPY requirements.txt .

RUN pip install -r requirements.txt

COPY . .

RUN chmod a+x docker/*.sh

ENV PYTHONPATH=/astro_bot/src