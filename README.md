# IoT Telemetry API

HTTP API that exposes the `iot_telemetry_data` table in PostgreSQL so the
front-end interface can read and modify telemetry records.

Built with FastAPI, psycopg 3, and Pydantic.

Each developer runs their own copy of the stack. The API and Postgres do
not need to be on the same network as the rest of the team. See section
9.4 if you're not on the same LAN as whoever is hosting the database.

> Troubleshooting errors encountered during development are documented
> separately in Jira under the API workstream. If something breaks, check
> there first before pinging the team.

---
## Running the Project with Docker

### Requirements

- Docker Desktop installed and running.
- The project repository cloned to your computer.
- A local PostgreSQL server with the required databases and tables.
- A root `.env` file with the database credentials.
### Configure environment variables

Create a `.env` file in the project root (the same folder as `docker-compose.yml`). Add your own database passwords:

```dotenv
DB_PASSWORD=your_postgres_password
CONTROL_DB_PASSWORD=your_control_database_password
GF_DATASOURCE_PASSWORD=your_grafana_database_password
```

Replace the example values with the correct credentials for your local setup. Do not commit this file to Git.

The telemetry database must be reachable on the configured `DB_PORT`, and the control settings database must be reachable on `CONTROL_DB_PORT`. The defaults are `5434` and `5432`, respectively, for the API. Check `docker-compose.yml` for service-specific settings.

### Start the project

Open PowerShell in the project folder and run:

```powershell
docker compose config --quiet
docker compose up -d --build
docker compose ps -a
```

The first command checks the configuration, the second builds and starts the services, and the third shows their status.

### Useful URLs

- Dashboard: `http://127.0.0.1:5500/Prototype/control_ui/index.html` (when VS Code Live Server is running).
- API documentation: `http://localhost:8000/docs`
- Kafka UI: `http://localhost:8081`
- Grafana: `http://localhost:3001`

### Stop the project

Run this from the project folder:

```powershell
docker compose down
```

### Troubleshooting

- If a port is already in use, check which application is using it before changing the port.
- If a container exits, check its logs with `docker compose logs --tail=40 SERVICE_NAME`.
- Keep database passwords in your local `.env` file. Never commit `.env` files to Git.


## 1. What this API does

It sits between the PostgreSQL database and the front-end interface.

    Front-end  ->  API (this folder)  ->  PostgreSQL
    (teammate)     (you, now)             (iot_telemetry_data table)

The front-end calls HTTP endpoints. This API translates those calls into SQL
and returns JSON.

Five endpoints:

| Method | Path                    | Purpose                                |
|--------|-------------------------|----------------------------------------|
| GET    | /telemetry              | List rows (query: limit, offset)       |
| GET    | /telemetry/{record_id}  | Fetch one row by records id            |
| POST   | /telemetry              | Insert a new row                       |
| PUT    | /telemetry/{record_id}  | Update specific fields on a row        |
| DELETE | /telemetry/{record_id}  | Delete a row                           |

---

## 2. Project layout

    Prototype/
    ├── .env                    <- DB credentials (gitignored, NOT committed)
    ├── .gitignore              <- ignores .env
    ├── requirements.txt        <- Python dependencies
    ├── Data_Sensor.py          <- MQTT publisher (separate workstream)
    └── api/
        ├── __init__.py
        ├── config.py           <- reads .env, builds DATABASE_URL
        ├── db.py               <- connection pool, get_connection()
        ├── models.py           <- Pydantic schemas (shape of a row)
        ├── routes.py           <- the five HTTP endpoints
        ├── errors.py           <- JSON error handlers for DB failures
        └── main.py             <- FastAPI app entry point

---

## 3. Setup — for teammates cloning the repo

### 3.1 Install Python 3.12 or newer

Python 3.11 will NOT work. The uvicorn version pulled in by the current
requirements file imports `typing.NotRequired`, which only exists from
Python 3.12 onward.

Install Python 3.13 (matches the machines we tested on):

    winget install --id Python.Python.3.13

Close every PowerShell/VS Code window afterwards and open a new one. Then:

    python --version      # should print Python 3.13.x

### 3.2 Clone the repo

    git clone https://github.com/D00281102/Devops_Group_Project.git

Then switch to your branch:

    git checkout Jo          # or Bright / Daniils / Simon — use your own

Branch names are case-sensitive.

### 3.3 Install the packages

From the repo root:

    pip install -r Prototype/requirements.txt

Or manually:

    pip install fastapi uvicorn "psycopg[binary]" python-dotenv psycopg_pool

### 3.4 Create your own `.env`

`.env` is gitignored on purpose — every machine has its own copy with its own
DB values. Create `Prototype/.env` with:

    DB_HOST=localhost
    DB_PORT=5434
    DB_NAME=postgres
    DB_USER=postgres
    DB_PASSWORD=<your postgres password>

Notes:
- `DB_HOST=localhost` if Postgres is on the same machine.
- `DB_HOST=192.168.1.6` if Postgres is on the other laptop on the network.
- `DB_NAME` must be the database that actually contains the
  `iot_telemetry_data` table. On our setup that's `postgres`.

### 3.5 Check Postgres is reachable

    psql -U postgres -h localhost -p 5434 -l

Should list databases. If `psql` isn't on PATH:

    & "C:\Program Files\PostgreSQL\17\bin\psql.exe" -U postgres -h localhost -p 5434 -l

Verify the table exists:

    psql -U postgres -h localhost -p 5434 -d postgres -c "\dt"

You should see `iot_telemetry_data` in the list.

If the table isn't there and you're on your own machine, see section 9.4
Option A for how to create it and load the CSV.

---

## 4. Running the API

From the `Prototype` folder:

    python -m uvicorn api.main:app --reload

You must be in `Prototype`, not the repo root — the import path
`api.main:app` resolves relative to the current directory.

You should see:

    INFO:     Uvicorn running on http://127.0.0.1:8000
    INFO:     Application startup complete.

No traceback, no "pool" errors = good.

### 4.1 Interactive API docs (free, auto-generated)

Open in a browser:

    http://127.0.0.1:8000/docs      <- Swagger UI (test requests here)
    http://127.0.0.1:8000/redoc     <- ReDoc (nice to read)

Use Swagger for testing. Click any endpoint, click **Try it out**, paste a
body, click **Execute**. It handles JSON formatting for you — do NOT try to
run the bash-style curl command that Swagger shows at the bottom.

---

## 5. Testing the endpoints

### Health check

    curl.exe http://127.0.0.1:8000/

Should return `{"status":"ok"}`.

### List rows

    curl.exe "http://127.0.0.1:8000/telemetry?limit=3"

Returns an array of row objects.

### Fetch one row

    curl.exe "http://127.0.0.1:8000/telemetry/1"

Returns a single object.

### POST / PUT / DELETE

Use the Swagger page at `/docs` — PowerShell mangles the quotes in a curl
JSON body. Or use `curl.exe` with a JSON file:

    curl.exe -X POST "http://127.0.0.1:8000/telemetry" ^
      -H "Content-Type: application/json" ^
      --data-binary "@body.json"

where `body.json` contains the JSON payload.

---

## 6. Configuration reference

Read from `Prototype/.env` by `api/config.py`:

| Variable    | Default     | Meaning                                       |
|-------------|-------------|-----------------------------------------------|
| DB_HOST     | localhost   | Postgres hostname or IP                       |
| DB_PORT     | 5434        | Postgres port                                 |
| DB_NAME     | postgres    | Database containing iot_telemetry_data        |
| DB_USER     | postgres    | Postgres user                                 |
| DB_PASSWORD | ""          | Postgres password (required)                  |

These are combined into a `DATABASE_URL` of the form:

    postgresql://USER:PASSWORD@HOST:PORT/DB_NAME

which the connection pool in `api/db.py` uses.

---

## 7. Error responses

All errors return JSON in the shape:

    {"detail": "...", "error": "..."}   (for DB errors)
    {"detail": "..."}                    (for validation / not-found)

| Status | When it happens                                     |
|--------|-----------------------------------------------------|
| 400    | PUT with an empty body (no fields to update)        |
| 404    | record_id doesn't exist in the table                |
| 409    | DB constraint violated (e.g. NOT NULL, wrong type)  |
| 422    | Request body failed validation (FastAPI auto)       |
| 503    | Database unreachable (pool couldn't connect)        |

The 422 responses come from FastAPI/Pydantic automatically — you don't need
to raise them yourself. The 503 and 409 come from `api/errors.py`.

---

## 8. Architecture notes — why it's built this way

### Connection pool, not one connection per request
`api/db.py` creates a single `ConnectionPool` at import time. Every request
borrows a connection and returns it when done. This avoids the cost of
opening a fresh TCP+auth connection for every request. Standard pattern for
web servers.

### Three separate Pydantic models
- `TelemetryRow` — what the API returns (includes `records`).
- `TelemetryCreate` — what the client sends for POST (no `records`; the DB
  generates it).
- `TelemetryUpdate` — all fields optional, defaults to `None`. Used with
  `model_dump(exclude_unset=True)` so PUT only updates the fields the client
  actually sent. Sending `{"temp": 25}` leaves everything else alone.

### `conn.commit()` is required
psycopg does not auto-commit. Any INSERT/UPDATE/DELETE must call
`conn.commit()` inside the connection block, or the change rolls back when
the connection returns to the pool.

### Parameterised SQL only
Every query uses `%s` placeholders and passes values as a tuple. The one
exception is the PUT route, which builds `SET col = %s, ...` from the keys
of a Pydantic model — those keys come from our code, not user input, so
they're safe. The values are still parameterised.

---

## 9. Network setup — if Postgres is on another machine

This section only applies if you're trying to reach the team's Postgres
over a network. If you're running your own Postgres locally, go straight to
section 9.4 Option A and ignore 9.1–9.3.

If the API runs on machine A and Postgres runs on machine B, three things
must be true on machine B (the Postgres machine):

### 9.1 `postgresql.conf` — allow external connections
`C:\Program Files\PostgreSQL\17\data\postgresql.conf`

Set:

    listen_addresses = '*'

(Remove the `#` at the start of the line.)

To check it's already listening externally:

    Get-NetTCPConnection -State Listen | Where-Object {$_.LocalPort -eq 5434}

If LocalAddress shows `0.0.0.0`, it's already accepting external connections.

### 9.2 `pg_hba.conf` — allow your network range
`C:\Program Files\PostgreSQL\17\data\pg_hba.conf`

Add as the **last line** of the file:

    host    all    all    192.168.1.0/24    scram-sha-256

Change `192.168.1.0/24` to match your network. Rules are matched top-down,
first match wins, so this line catches everything the localhost rules don't.

Edit with Notepad run as Administrator (right-click Notepad → Run as admin).

### 9.3 Windows Firewall — open the port
In an Administrator PowerShell on the Postgres machine:

    New-NetFirewallRule -DisplayName "Postgres 5434" -Direction Inbound -Protocol TCP -LocalPort 5434 -Action Allow

Restart Postgres afterwards:

    Restart-Service postgresql-x64-17

Then on machine A, set `DB_HOST=<B's IP>` in `.env`.

### 9.4 If you are NOT on the same network as the Postgres machine

Everything in 9.1–9.3 only works when both machines are on the same LAN
(same Wi-Fi, same home network). If your machine is somewhere else —
different house, college network, mobile hotspot — the connection will time
out no matter how Postgres is configured.

**Before you read any further**: Option A below sets up a completely fresh,
independent stack on your own machine. If you take that route, everything
you already did in sections 3.1–3.3 still applies (Python, clone, packages).
Section 3.4 onwards changes, because you'll be pointing at your own
database, not the team's. Work through section 9.4 Option A and then come
back to section 4 to run the API.

You have three options. Pick the one that fits.

**Option A — Load the CSV into your own local Postgres (recommended)**

This is the cleanest option. You don't need anyone else's machine.

1. Install Postgres on your own machine (port 5434 to match the team setup,
   or whatever you want — you control it).

2. Get the CSV file. It's `iot_telemetry_data.csv` and should be in the
   repo, under `Prototype/data/`. If it's not there, ask the team.

3. Create the table. In psql:

       psql -U postgres -h localhost -p 5434 -d postgres

   Then paste:

       CREATE TABLE iot_telemetry_data (
           records  SERIAL PRIMARY KEY,
           ts       DOUBLE PRECISION NOT NULL,
           device   TEXT NOT NULL,
           co       DOUBLE PRECISION NOT NULL,
           humidity DOUBLE PRECISION NOT NULL,
           light    BOOLEAN NOT NULL,
           lpg      DOUBLE PRECISION NOT NULL,
           motion   BOOLEAN NOT NULL,
           smoke    DOUBLE PRECISION NOT NULL,
           temp     DOUBLE PRECISION NOT NULL
       );

   (If a teammate already has this table, run `\d iot_telemetry_data` on
   their machine to get the exact column types and match them. Mismatched
   types cause confusing errors later.)

4. Load the CSV. Easiest way is pgAdmin:

   - Open pgAdmin, connect to your local server.
   - Right-click `iot_telemetry_data` → **Import/Export Data**.
   - Mode: Import. Filename: point at the CSV. Format: csv. Header: Yes.
   - Columns: match the CSV's column order to the table's columns.
   - Click OK.

   Or from psql (faster if you're comfortable):

       \copy iot_telemetry_data (ts, device, co, humidity, light, lpg, motion, smoke, temp) FROM 'C:/path/to/iot_telemetry_data.csv' WITH (FORMAT csv, HEADER true);

   Note: `\copy` needs forward slashes even on Windows.

5. Set your `.env`:

       DB_HOST=localhost
       DB_PORT=5434
       DB_NAME=postgres
       DB_USER=postgres
       DB_PASSWORD=<your own password>

6. **Now go back to section 4** and start the API as normal. Everything from
   section 4 onwards works exactly the same; it just talks to your own
   database instead of the team's.

You now have a fully independent dev environment. Nothing depends on anyone
else's machine.

**Option B — Run Postgres in Docker on your own machine**

If you have Docker, this skips the Postgres installer entirely:

    docker run --name iot-postgres -e POSTGRES_PASSWORD=yourpassword -p 5434:5432 -d postgres:17

Then load the CSV into it the same way as Option A steps 3–4. `.env` stays
as `DB_HOST=localhost`, `DB_PORT=5434`. Once your container is up, go back
to section 4 to run the API.

Your repo already has a `docker-compose.yml` — check whether it already
defines a Postgres service before starting a separate container.

**Option C — Tunnel to the Postgres machine**

Only worth doing if you specifically need to see the same data everyone
else sees, live. Tools like Tailscale or ngrok create a private network
between machines across the internet. This adds setup and security
considerations and isn't needed for development. Avoid unless you have a
specific reason.

**What NOT to do**

Do not try to expose Postgres directly to the public internet by
port-forwarding on your router. Postgres has no business being reachable
from the open internet, and you'll get scanned and attacked within hours.
If you need remote access, use a tunnel (Option C), never a port forward.

---

## 10. What the front-end teammate needs to know

- Base URL when running locally: `http://127.0.0.1:8000`
- All responses are JSON.
- Data shape: see `api/models.py`, or open `/docs` and look at the schemas.
- Field names are exactly as in the table: `records`, `ts`, `device`, `co`,
  `humidity`, `light`, `lpg`, `motion`, `smoke`, `temp`.
- `light` and `motion` are booleans. Everything else numeric is a float
  except `records` (integer) and `device` (string).
- Pagination on the list endpoint: `?limit=100&offset=0`. Defaults are
  100 and 0.
- Errors: always check the HTTP status code. 4xx = your request, 5xx =
  server/DB side. Body always has a `detail` field.
- For testing the API without writing client code, use
  `http://127.0.0.1:8000/docs`.

---

## 11. Git workflow

- Work on your own branch (`Jo`, `Bright`, `Daniils`, `Simon`, ...).
- Push to your branch: `git push origin <branch>`.
- Do NOT push directly to `main` after this point.
- To merge your work into `main`: open a Pull Request on GitHub, get it
  reviewed, then merge.
- Never commit `.env`. It's gitignored — if `git status` shows it, something
  is wrong with `.gitignore`.

---

## 12. Quick reference

Start the server:

    cd Prototype
    python -m uvicorn api.main:app --reload

Test in browser:

    http://127.0.0.1:8000/docs

Test in terminal:

    curl.exe "http://127.0.0.1:8000/telemetry?limit=3"

Stop the server:

    Ctrl+C in the terminal running uvicorn

List databases:

    psql -U postgres -h localhost -p 5434 -l

List tables in `postgres`:

    psql -U postgres -h localhost -p 5434 -d postgres -c "\dt"

View all telemetry rows directly in SQL:

    psql -U postgres -h localhost -p 5434 -d postgres -c "SELECT * FROM iot_telemetry_data LIMIT 10;"