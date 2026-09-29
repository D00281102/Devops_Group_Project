# Grafana Visualisation Documentation

## 1. Overview

Grafana was selected as the visualisation tool for the IoT project.

The purpose of the Grafana work was to investigate how sensor data could be displayed and monitored using dashboards and time-series visualisations.

The planned project data flow is:

```text
IoT Sensor Dataset
        ↓
Python Sensor Simulator
        ↓
MQTT Broker (Mosquitto)
        ↓
Kafka Connect
        ↓
Apache Kafka
        ↓
PostgreSQL / TimescaleDB
        ↓
Grafana


2. The Grafana Docker image used was:

```text
grafana/grafana:latest
```

The following command was used to create and run the Grafana container:

```powershell
docker run -d --name grafana -p 3000:3000 grafana/grafana:latest
```

The container was created with Grafana exposed on port 3000.

The container was named:

```text
grafana
```

Grafana was accessed locally through:

```text
http://localhost:3000
```

The Grafana version tested during the project was:

```text
Grafana 13.2.2
```

The Docker container was later stopped when it was no longer needed for testing. The container can be started again using:

```powershell
docker start grafana
```


**3. Grafana Testing**

After installing Grafana, the built-in Grafana TestData data source was used to test the visualisation functionality.

TestData was used because the project's PostgreSQL database connection had not yet been completed at this stage.

The TestData data source allowed time-series data to be generated and displayed in Grafana without requiring the project's live database.

This confirmed that Grafana could successfully display time-series data in a dashboard.


**4. Test Dashboard**

A test dashboard was created to evaluate the visualisation capabilities of Grafana.

The dashboard was named:

IoT Sensor Data - Grafana Test

A time-series panel was created with the name:

Sensor Data Time Series

The panel was used to display the sensor-style time-series data generated through Grafana's TestData data source.

The dashboard was created as an initial test before connecting Grafana to the project's PostgreSQL database.


**5. Dashboard Testing**

The Grafana TestData data source was used to generate test data and verify the dashboard.

The test confirmed that:

Grafana was successfully installed and accessible.
A dashboard could be created.
A time-series panel could be added.
Test sensor-style data could be displayed over time.
Grafana could be used as the visualisation layer for the IoT project.

The TestData source was only used for testing the Grafana visualisation functionality.

It does not represent the project's actual sensor dataset.

**6. Local PostgreSQL Testing**

A local PostgreSQL database was set up to test the Grafana database connection before using the project's shared database.

PostgreSQL version tested:

PostgreSQL 17.11

The local PostgreSQL server used:

localhost:5432

The PostgreSQL service can be checked in PowerShell using:

Get-Service *postgres*

The PostgreSQL service should show a status of:

Running

The PostgreSQL port was also tested using:

Test-NetConnection localhost -Port 5432

The test was successful when:

TcpTestSucceeded : True
**7. Creating the Dummy Sensor Table**

A local PostgreSQL table was created for testing Grafana with dummy sensor data.

The table was called:

dummy_sensor_data

The following SQL was used:

CREATE TABLE dummy_sensor_data (
    id SERIAL PRIMARY KEY,
    ts TIMESTAMP NOT NULL,
    device VARCHAR(50),
    temp DOUBLE PRECISION,
    humidity DOUBLE PRECISION,
    light DOUBLE PRECISION,
    co DOUBLE PRECISION,
    lpg DOUBLE PRECISION,
    motion BOOLEAN,
    smoke DOUBLE PRECISION
);

The table contains the following sensor fields:

id
ts
device
temp
humidity
light
co
lpg
motion
smoke
**8. Inserting Dummy Sensor Data**

Five dummy sensor readings were inserted into the local PostgreSQL table.

The following SQL was used:

INSERT INTO dummy_sensor_data
(ts, device, temp, humidity, light, co, lpg, motion, smoke)
VALUES
('2026-09-29 14:00:00', 'sensor-01', 22.5, 48.2, 350, 0.4, 1.2, true, 0.1),
('2026-09-29 14:05:00', 'sensor-01', 23.1, 49.0, 370, 0.5, 1.3, false, 0.1),
('2026-09-29 14:10:00', 'sensor-01', 23.8, 50.1, 390, 0.5, 1.4, true, 0.2),
('2026-09-29 14:15:00', 'sensor-01', 24.2, 51.3, 410, 0.6, 1.5, false, 0.2),
('2026-09-29 14:20:00', 'sensor-01', 24.8, 52.0, 430, 0.7, 1.6, true, 0.3);

The insert was successful when PostgreSQL returned:

INSERT 0 5
**9. Checking the Dummy Data**

The inserted data was checked using:

SELECT *
FROM dummy_sensor_data
ORDER BY ts;

The query returned the five dummy sensor readings successfully.

The temperature values used for the test were:

22.5
23.1
23.8
24.2
24.8

This confirmed that the dummy sensor data was stored correctly in PostgreSQL.

**10. Connecting Grafana to PostgreSQL**

Grafana was connected to the local PostgreSQL database using the PostgreSQL data source.

The Grafana PostgreSQL connection used:

Host: host.docker.internal:5432
Database: postgres
Username: postgres
Password: admin
SSL Mode: disable
PostgreSQL Version: 17

The password is included here only to document the local test setup. The local database used a test password and this should not be used for a shared or production database.

Grafana's Save & test function returned:

Database Connection OK

This confirmed that Grafana could communicate with the local PostgreSQL database.

**11. Querying PostgreSQL Data from Grafana**

The PostgreSQL data source was selected in Grafana Explore.

The following SQL query was used:

SELECT
    ts AS "time",
    temp
FROM dummy_sensor_data
ORDER BY ts;

The query returned the five temperature readings from PostgreSQL.

Grafana displayed the results as a time-series graph.

The graph showed the temperature increasing from:

22.5

to:

24.8

This confirmed that Grafana could read data from PostgreSQL and display it as a visualisation.

**12. Creating the Grafana Dashboard**

The working PostgreSQL query was added to a Grafana dashboard.

The dashboard was named:

IoT Sensor Data Dashboard

The panel was named:

Temperature Readings

The panel displayed the five dummy PostgreSQL temperature readings as a time-series graph.

The dashboard was saved successfully.

**13. Dashboard Verification**

After saving the dashboard, the browser was refreshed.

The dashboard loaded again successfully and the:

Temperature Readings

panel continued to display the PostgreSQL dummy data.

This confirmed that the dashboard was saved correctly and was still working after a refresh.

**Grafana installed using Docker.
Grafana accessed through port 3000.
Grafana version 13.2.2 tested.
Grafana TestData data source tested.
Initial Grafana test dashboard created.
PostgreSQL 17.11 installed locally.
PostgreSQL service verified as running.
PostgreSQL port 5432 tested successfully.
Local dummy_sensor_data table created.
Five dummy sensor readings inserted.
Dummy sensor data verified using SQL.
Grafana PostgreSQL data source configured.
Grafana successfully connected to local PostgreSQL.
PostgreSQL sensor data queried from Grafana.
Temperature data displayed as a time-series graph.
IoT Sensor Data Dashboard created and saved.
Temperature Readings panel created.
Dashboard refreshed and verified successfully.**
