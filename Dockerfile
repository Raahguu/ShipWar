FROM python:alpine

WORKDIR /app
COPY server.py .

RUN pip install websockets

EXPOSE 8765

CMD ["python", "server.py"]