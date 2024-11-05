FROM python:slim

COPY requirements.txt requirements.txt
RUN pip install --no-cache-dir -r requirements.txt
RUN pip install pymysql cryptography

COPY app app
COPY migrations migrations
COPY travel-planner.py config.py entrypoint.sh ./
RUN chmod a+x entrypoint.sh

ENV FLASK_APP=travel-planner.py

EXPOSE 5000
ENTRYPOINT ["./entrypoint.sh"]
