FROM python:3.12-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

EXPOSE 5000

ENV PORT=5000
ENV FLASK_DEBUG=false

CMD ["gunicorn", "-b", "0.0.0.0:5000", "-w", "2", "--timeout", "90", "app:app"]
