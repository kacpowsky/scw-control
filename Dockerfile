FROM scaleway/cli:latest

RUN apk add --no-cache python3

COPY run.py /app/run.py

ENTRYPOINT ["python3", "/app/run.py"]
