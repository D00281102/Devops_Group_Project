# Grafana Visualisation Documentation

## 1. Overview

Grafana is used in the IoT project to display and monitor sensor data stored in PostgreSQL.

It provides dashboards and graphs for visualising temperature, humidity, gas levels, motion and light readings.

Grafana runs as a Docker container and uses PostgreSQL as its data source.

## 2. Requirements

Before running Grafana, make sure you have:

- Docker Desktop installed and running.
- PostgreSQL 17 installed and running, with the project database and required tables available.
- The project repository cloned.
- A local `.env` file configured with the required database credentials.

## 3. Grafana Project Files

The Grafana configuration files are stored in:

```text
Prototype/grafana/
│
├── dashboards/
│   └── iot-sensor-dashboard.json
│
├── provisioning/
│   ├── dashboards/
│   │   └── dashboard-provider.yml
│   │
│   └── datasources/
│       └── postgres.yml
```

These files are used to automatically load the dashboard and configure the PostgreSQL data source.

## 4. Configuration

Grafana connects to PostgreSQL using the Docker host address:

```text
host.docker.internal:5432
```

The PostgreSQL password is supplied through the local `.env` file using:

```env
GF_DATASOURCE_PASSWORD=your_database_password
```

Use the appropriate local database credentials. Do not commit your `.env` file to Git.

## 5. Running Grafana

From the project root directory, start the services using:

```powershell
docker compose up -d
```

Check that Grafana is running:

```powershell
docker compose ps grafana
```

Grafana can be accessed through:

```text
http://localhost:3001
```

## 6. Dashboard Verification

The project dashboard is called:

**IoT Sensor Data - Real Project**

It contains eight panels:

1. Temperature Readings
2. Humidity Readings
3. CO Readings
4. LPG Readings
5. Smoke Readings
6. Current Motion Status
7. Current Light Status
8. Current Temperature

To verify the PostgreSQL connection:

1. Open Grafana.
2. Go to Connections → Data sources.
3. Open the provisioned PostgreSQL data source.
4. Use Save & test if available.
5. Confirm that Grafana displays `Database Connection OK`.

The dashboard should then display the available sensor readings.

## 7. Important Notes

- The dashboard is loaded from the project JSON file.
- The PostgreSQL data source is configured through provisioning.
- Changes to the dashboard should be made in the project JSON file.
- Database passwords must be kept in the local `.env` file.
- PostgreSQL must be running and accessible on port 5432 before Grafana can retrieve sensor data.