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
