FROM python:alpine

WORKDIR /app
COPY Server.py .

RUN pip install websockets

EXPOSE 8765

CMD ["python", "Server.py"]
