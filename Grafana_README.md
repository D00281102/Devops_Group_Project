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


3. Grafana Testing

After installing Grafana, the built-in Grafana TestData data source was used to test the visualisation functionality.

TestData was used because the project's PostgreSQL database connection had not yet been completed at this stage.

The TestData data source allowed time-series data to be generated and displayed in Grafana without requiring the project's live database.

This confirmed that Grafana could successfully display time-series data in a dashboard.


4. Test Dashboard

A test dashboard was created to evaluate the visualisation capabilities of Grafana.

The dashboard was named:

IoT Sensor Data - Grafana Test

A time-series panel was created with the name:

Sensor Data Time Series

The panel was used to display the sensor-style time-series data generated through Grafana's TestData data source.

The dashboard was created as an initial test before connecting Grafana to the project's PostgreSQL database.


5. Dashboard Testing

The Grafana TestData data source was used to generate test data and verify the dashboard.

The test confirmed that:

Grafana was successfully installed and accessible.
A dashboard could be created.
A time-series panel could be added.
Test sensor-style data could be displayed over time.
Grafana could be used as the visualisation layer for the IoT project.

The TestData source was only used for testing the Grafana visualisation functionality.

It does not represent the project's actual sensor dataset.

6. Current Status

The Grafana installation and initial dashboard testing have been completed.

The following work has been completed:

Grafana installed using Docker.
Grafana accessed through port 3000.
Grafana version 13.2.2 tested.
Grafana TestData data source tested.
IoT Sensor Data - Grafana Test dashboard created.
Sensor Data Time Series panel created.
Time-series visualisation successfully tested.

At this stage, the dashboard is using Grafana TestData rather than the project's PostgreSQL database.

7. Next Step

The next stage is to connect Grafana to the project's PostgreSQL database containing the IoT sensor data.

The database information provided by the project documentation is:

Database: postgres
Port: 5434
Table: iot_telemetry_data

The database contains the project's IoT telemetry data.

Once the database connection is available, Grafana can be configured to query the actual sensor data instead of the TestData source.

The ts field in the database contains Unix timestamp values, so Grafana queries will need to convert these values into timestamps when creating time-series visualisations.

Example:

SELECT
    to_timestamp(ts) AS "time",
    temp
FROM iot_telemetry_data
ORDER BY ts;

Further Grafana dashboards and panels can then be developed using the project's actual sensor data.

8. Future Analytics Work

The visualisation work can also be extended to analytics.

Possible areas for investigation include:

Sensor readings over time
Temperature trends
Humidity trends
CO and smoke readings
LPG readings
Device-level comparisons
Sensor activity and changes over time
Identifying unusual or abnormal readings

Further research will be carried out to investigate suitable analytics approaches and how they can be integrated with the project's visualisation stage.
