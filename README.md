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
