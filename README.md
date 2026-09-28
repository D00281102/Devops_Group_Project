# Devops_Group_Project

# IoT Telemetry — Database Access Guide

This document contains everything you need to connect to the shared PostgreSQL
database that holds the `iot_telemetry_data` dataset.

---

## 1. Connection Details

| Item           | Value                                              |
|----------------|----------------------------------------------------|
| Host           | `192.168.1.8` (LAN IP — update if it changes)      |
| Port           | `5434`                                             |
| Database       | `postgres`                                         |
| User           | `postgres`                                         |
| Password       | *(ask the DB owner — not stored in this repo)*     |
| Table          | `iot_telemetry_data`                               |
| Rows           | 405,184                                            |
| TimescaleDB    | Installed (v2.30.1), but table is a regular table  |

**Connection string (for Python, JDBC, etc.):**

> The port is **5434**, not the default 5432. Do not omit it.

---

## 2. Table Schema

The table has 10 columns. The first column, `records`, is auto-generated.

| Column     | Type              | Notes                                    |
|------------|-------------------|------------------------------------------|
| `records`  | integer           | Auto-generated (1 … 405,184)             |
| `ts`       | double precision  | Unix timestamp (seconds, with decimals)  |
| `device`   | text              | MAC address of the sensor                |
| `co`       | double precision  | Carbon monoxide reading                  |
| `humidity` | double precision  | Humidity percentage                      |
| `light`    | boolean           | true / false                             |
| `lpg`      | double precision  | LPG reading                              |
| `motion`   | boolean           | true / false                             |
| `smoke`    | double precision  | Smoke reading                            |
| `temp`     | double precision  | Temperature in Celsius                   |

> `records` is `GENERATED ALWAYS AS IDENTITY`. Do **not** insert a value into
> it — PostgreSQL fills it automatically.

> `ts` is a Unix epoch timestamp, not a date type. Convert it in SQL with
> `to_timestamp(ts)` if you need a readable date.

---

## 3. For the Kafka Engineer

You are producing/consuming messages that will be written to the
`iot_telemetry_data` table (or read from it).

- **Do not include the `records` column** in anything you send. PostgreSQL manages it.
- Your JDBC sink connector will need:
  - `connection.url` → `jdbc:postgresql://192.168.1.8:5434/postgres` - check connection details again if the URL is not working
  - `connection.user` → `postgres`
  - `connection.password` → *(get from DB owner)*
- Kafka Connect JDBC sink does **not** support `GENERATED ALWAYS AS IDENTITY` in
  `insert.mode=upsert` cleanly. Use `insert.mode=insert` if you are only adding
  new rows, or drop the identity behaviour if you need upserts.
- The table name for the connector is `iot_telemetry_data`.
- The `light` and `motion` columns are **boolean**. Make sure your Kafka
  schema treats them as such, or the insert will fail.

- Test by sending one message and querying the table from psql:
   SELECT * FROM iot_telemetry_data ORDER BY records DESC LIMIT 5;

---

## 4. For the Visualisation Engineer

You only need **read access**.

- Connect your tool (Confluent, Metabase, Grafana, Tableau, whatever) using the
  connection string in section 1.
- Example starting query:
  ```sql
  SELECT *
  FROM iot_telemetry_data
  ORDER BY records
  LIMIT 100;

------------------------------------------------------------------------
5. FOR EVERYONE ELSE (CONNECTIVITY REFERENCE — COLLEGE NETWORK ONLY)
------------------------------------------------------------------------

IMPORTANT: This setup only works when everyone is physically in
college, connected to the same campus network. If you are at home,
on a phone hotspot, or on any other network, you will not be able to
reach the database. In that case, contact the DB owner — the
connection method changes and a private VPN (Tailscale) would be
needed instead.

BEFORE YOU TRY TO CONNECT

  1. Make sure you are in college and connected to the same campus
     WiFi or wired network as the DB host. Do not try this from home.
  2. Ask the DB owner for two things:
        - The host machine's campus LAN IP address (looks like 192.168.x.x)
        - The postgres password

CONNECTION DETAILS

    Item           | Value
    ---------------+--------------------------------------------------
    Host           | The DB host's LAN IP (e.g. 192.168.1.8)
    Port           | 5434
    Database       | postgres
    User           | postgres
    Password       | (ask the DB owner)
    Table          | iot_telemetry_data

Connection string:

    postgresql://postgres:YOUR_PASSWORD@<LAN_IP>:5434/postgres

Test from your terminal:

    psql -h <LAN_IP> -p 5434 -U postgres

IF IT TIMES OUT

  - Confirm you are actually in college and on the campus network,
    not tethered to a phone or on a home connection.
  - Confirm you are on the same subnet as the DB host. Ask the DB
    owner to run ipconfig on their machine and compare the first
    three numbers of your IP and theirs.
  - Ping the host machine first:

        ping <LAN_IP>

    If the ping fails while you are on campus, the campus network
    is likely blocking device-to-device traffic (common on
    college WiFi). In that case, tell the DB owner — the solution
    is a wired connection, a shared phone hotspot, or installing
    Tailscale as a fallback.

  - If ping works but psql still fails, the DB host's firewall or
    pg_hba.conf is not allowing your IP. Tell the DB owner so they
    can add your campus IP range to the allowed list.


