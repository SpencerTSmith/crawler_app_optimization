FROM python:3.11-slim

RUN apt-get update && apt-get install -y gcc libpq-dev

COPY requirements.txt requirements.txt
RUN pip install -r requirements.txt
RUN pip install gunicorn pymysql cryptography

COPY app app
COPY migrations migrations
COPY microblog.py config.py boot.sh ./
RUN chmod a+x boot.sh

ENV FLASK_APP microblog.py
RUN flask translate compile

EXPOSE 8069
ENTRYPOINT ["./boot.sh"]
