FROM python:alpine

WORKDIR /app
COPY Server.py .

RUN pip install websockets

EXPOSE 6363

CMD ["python", "Server.py Docker"]