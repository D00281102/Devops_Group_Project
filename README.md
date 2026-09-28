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
5. NETWORK SETUP — CAMPUS WI-FI
------------------------------------------------------------------------

Everyone, including the DB host, must be on the same campus Wi-Fi
network. There is no VPN involved.

========================================================================
5A. WHAT THE DB OWNER DOES

STEP 1 — Find your current campus Wi-Fi IP

WHERE: PowerShell window (PS C:\WINDOWS\system32>)

    ipconfig

WHAT IT DOES: Lists every network adapter on your machine. Look for
the adapter labelled "Wireless LAN adapter Wi-Fi" and find the line
that says "IPv4 Address". It will look something like:

    IPv4 Address. . . . . . . . . . . : 10.20.30.45

Write that number down. This is the IP you will give to your teammates.

STEP 2 — Update pg_hba.conf to allow the campus network

WHERE: Notepad, opened as Administrator

File to edit:
    C:\Program Files\PostgreSQL\17\data\pg_hba.conf

Find the line:
    host all all 192.168.1.0/24 scram-sha-256

Replace it with the campus network range. If your IP is 10.20.30.45,
the line becomes:
    host all all 10.20.30.0/24 scram-sha-256

WHAT IT DOES: Tells PostgreSQL which remote IP addresses are allowed
to connect. Without this, anyone outside 192.168.1.x (i.e. everyone
on campus) is rejected.

STEP 3 — Confirm postgresql.conf is listening on all interfaces

WHERE: Notepad, opened as Administrator

File to edit:
    C:\Program Files\PostgreSQL\17\data\postgresql.conf

Find the line:
    listen_addresses = '*'

If it is not already set to '*', change it to that.

WHAT IT DOES: Makes PostgreSQL accept connections on every network
interface, not just localhost.

STEP 4 — Open the Windows Firewall for port 5434

WHERE: Windows Defender Firewall with Advanced Security

  1. Windows key -> type "Windows Defender Firewall with Advanced
     Security" -> Enter
  2. Click "Inbound Rules" on the left
  3. Click "New Rule..." on the right
  4. Select "Port" -> Next
  5. Select "TCP", enter "5434" in "Specific local ports" -> Next
  6. Select "Allow the connection" -> Next
  7. Tick Domain, Private, Public -> Next
  8. Name it "PostgreSQL 5434" -> Finish

WHAT IT DOES: Lets other machines on the campus Wi-Fi reach your
PostgreSQL port. Without this, the connection times out even if
PostgreSQL is running.

STEP 5 — Restart PostgreSQL

WHERE: Windows Services

  1. Windows key -> type "Services" -> Enter
  2. Find "postgresql-x64-17"
  3. Right-click -> Restart

WHAT IT DOES: Reloads the config files you just edited. Changes to
pg_hba.conf and postgresql.conf do not apply until the service
restarts.

STEP 6 — Send your teammates the connection details

    Host:     <your campus IPv4 address>  (e.g. 10.20.30.45)
    Port:     5434
    Database: postgres
    User:     postgres
    Password: (your password — send securely, not on a public channel)
    Table:    iot_telemetry_data

========================================================================
5B. WHAT THE TEAMMATES DO


STEP 1 — Connect to the same campus Wi-Fi as the DB host

WHAT IT DOES: The database is only reachable from inside the campus
network. If you are on mobile data or a different Wi-Fi, the
connection will fail.

STEP 2 — Test the network path

WHERE: PowerShell window (PS C:\WINDOWS\system32>)

    ping <DB_HOST_IP>

Replace <DB_HOST_IP> with the IP the DB owner gave you. Example:

    ping 10.20.30.45

WHAT IT DOES: Sends a small packet to the DB host to confirm you can
reach it at all.

  - Replies received -> good, move on.
  - "Request timed out" -> you are on the wrong Wi-Fi, or the DB
    owner's firewall is still blocking. Tell the DB owner.

STEP 3 — Test the database connection

WHERE: PowerShell window (PS C:\WINDOWS\system32>)

    psql -h <DB_HOST_IP> -p 5434 -U postgres

Enter the password the DB owner gave you when prompted. You should
land at postgres=#.

WHAT IT DOES: Attempts a real connection to PostgreSQL using the
credentials the DB owner provided.

  - If you get postgres=# -> you are connected.
  - "Connection refused" -> PostgreSQL is not running or not
    listening on 5434.
  - "Connection timed out" -> firewall still blocking.
  - "password authentication failed" -> wrong password.

STEP 4 — Verify you can see the data

WHERE: postgres=# prompt

    SELECT COUNT(*) FROM iot_telemetry_data;

WHAT IT DOES: Confirms the table exists and is populated. Should
return 405184.

STEP 5 — Exit

WHERE: postgres=# prompt

    \q

WHAT IT DOES: Closes the psql session.

NOTE: The DB host IP changes between networks (home vs campus). If
your connection suddenly stops working, ask the DB owner for the new
IP — do not assume the old one still works.


