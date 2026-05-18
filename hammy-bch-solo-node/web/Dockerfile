FROM python:3.12-alpine

WORKDIR /app

COPY server.py /app/server.py
COPY index.html /app/static/index.html
COPY styles.css /app/static/styles.css
COPY script.js /app/static/script.js

EXPOSE 3000

CMD ["python", "/app/server.py"]
