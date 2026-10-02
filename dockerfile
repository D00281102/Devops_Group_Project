FROM python:3.12-slim

WORKDIR /app

COPY Prototype/requirements.txt .

RUN pip install --no-cache-dir -r requirements.txt

COPY Prototype/Data_Sensor.py .
COPY Prototype/data ./data

CMD ["python", "Data_Sensor.py"]