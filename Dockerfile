FROM python:slim

COPY requirements.txt requirements.txt
RUN pip install -r requirements.txt
RUN pip install pymysql cryptography flask-migrate gunicorn

COPY app app
COPY migrations migrations
COPY travel-planner.py config.py entrypoint.sh wait-for-it.sh ./
RUN chmod a+x entrypoint.sh wait-for-it.sh

ENV FLASK_APP=travel-planner.py
ENV FLASK_RUN_HOST=0.0.0.0

EXPOSE 5000
ENTRYPOINT ["./entrypoint.sh"]
