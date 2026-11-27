# Containerised IoT and Kafka Setup

This guide covers the project's Docker Compose setup, including PostgreSQL
with a persistent data volume, Kafka, Kafka UI, the Python MQTT-to-Kafka bridge, Mosquitto,
the Sensor Simulator, Control Logic, Actuator Simulator, the Control API,
and Grafana. The Windows-hosted Kafka consumer can also write telemetry to
the PostgreSQL container through the published host port.

The current Compose stack uses a Python bridge for MQTT-to-Kafka forwarding;
the previous Kafka Connect plugin setup is no longer required.

For the current containerised Sensor Simulator, Control Logic, Actuator Simulator and Mosquitto setup, see **Dockerised IoT Control System — SCRUM-102** further down this document.

For the original manual Windows setup, see [local-setup.md](local-setup.md).

## Architecture
```text
Sensor Simulator (Docker) or Data_Sensor.py (Windows)
    |
    | MQTT: mosquitto:1883 (Docker) or localhost:1883 (Windows)
    v
Mosquitto in Docker
    |
    | MQTT: mosquitto:1883
    v
Python MQTT-to-Kafka bridge in Docker
    |
    | Kafka: kafka:9093
    v
Kafka in Docker
    |
    +--> Kafka UI in Docker: http://localhost:8081
    |
    +--> Database consumer on Windows
              |
              v
        PostgreSQL in Docker
        (`iot_telemetry_data`, persistent volume)
```

## Prerequisites
Install and start:

- Docker Desktop

- Python 3

Mosquitto does not need to be installed or started separately. Compose runs
it using the configuration file at:

```text

Prototype/mosquitto.conf

```

The startup script creates Kafka topics through `kafka-python`; neither a
local Kafka installation nor command-line tools inside the container are
required.

The dataset must be located at:

```text

Prototype/data/iot_telemetry_data.csv

```

Install the Python dependency:

```powershell

py -m pip install -r Prototype/requirements.txt

```

## PostgreSQL databases and initialization

Compose runs one PostgreSQL server with persistent storage in the
`postgres_data` volume. It initializes the telemetry database (the `DB_NAME`,
`postgres` by default) and a separate `control_settings_db`. Authentication
and control tables share `control_settings_db`, matching the combined
SCRUM-111 schema and the application's building/device relationships.

The `database-init` service creates the control database if needed, then
idempotently initializes the telemetry table, default control settings, and
authentication/building tables. The API and Control Logic wait for that
service to complete before starting. The initializer can also run against an
existing PostgreSQL volume without deleting its data.

Create `Prototype/.env` from `.env.example`, set `DB_PASSWORD` and
`AUTH_SECRET_KEY` to private values, and set `CONTROL_DB_PASSWORD` and
`AUTH_DB_PASSWORD` to the same PostgreSQL password. Start the stack from the
repository root:

```powershell
docker compose --env-file Prototype/.env up -d
```

Windows-hosted applications connect at `localhost:5434`; Compose services
connect to `postgres:5432`. Do not run `docker compose down -v` unless you
intend to delete the persistent PostgreSQL data.

Confirm both databases and their tables were initialized:

```powershell
docker compose --env-file Prototype/.env exec postgres psql -U postgres -d postgres -c "\dt"
docker compose --env-file Prototype/.env exec postgres psql -U postgres -d control_settings_db -c "\dt"
```

## Move the existing database into Docker

Back up the existing local PostgreSQL database before stopping it. Run from
the repository root while local PostgreSQL is running:

```powershell
New-Item -ItemType Directory -Force .\Prototype\data
pg_dump -h localhost -p 5434 -U postgres -d postgres --no-owner --no-acl -f .\Prototype\data\telemetry-backup.sql
```

The backup path is gitignored because it contains database data. If local
PostgreSQL occupies port 5434, stop its Windows service after creating the
backup. For PostgreSQL 17, run Administrator PowerShell:

```powershell
Stop-Service postgresql-x64-17
```

Start the PostgreSQL container with the credentials from `Prototype/.env`:

```powershell
docker compose --env-file Prototype/.env up -d postgres
```

For an empty Docker volume, wait until the telemetry backup has been restored
before starting `database-init`; the initializer creates the telemetry table.

Wait for `docker compose --env-file Prototype/.env ps postgres` to show the
container as healthy.

Restore the backup into the container:

```powershell
psql -h localhost -p 5434 -U postgres -d postgres -v ON_ERROR_STOP=1 -f .\Prototype\data\telemetry-backup.sql
```

Then initialize the remaining tables and the control/authentication database:

```powershell
docker compose --env-file Prototype/.env run --rm database-init
```

The compose service keeps the database in the `postgres_data` named volume.
Restarting or running `docker compose --env-file Prototype/.env down`
preserves the data. Avoid `docker compose --env-file Prototype/.env down -v`,
which deletes that volume.

## Network Addresses
Windows applications use the ports:

```text

Kafka: 127.0.0.1:9092

MQTT: localhost:1883

Kafka UI: http://localhost:8081
```

Docker containers use these internal addresses:

```text

Kafka: kafka:9093

MQTT: mosquitto:1883

```

Kafka UI is configured to use `kafka:9093` in `docker-compose.yml`.
The Windows API and database consumer connect to PostgreSQL at
`localhost:5434`, as configured in `Prototype/.env`. Other Docker services
can connect to PostgreSQL using `postgres:5432`.

## Start the Kafka Services Automatically
From the project root:

The Kafka startup script starts PostgreSQL, Mosquitto, Kafka, Kafka UI,
the MQTT-to-Kafka bridge, the Kafka topic, and a Python consumer
that writes records into the same PostgreSQL
`iot_telemetry_data` table. The consumer uses the `Prototype/.env` settings
shared with the API. Mosquitto uses the project's `Prototype/mosquitto.conf`
configuration.

Run it from the project root:

```powershell
Set-Location "C:\Devops_Group_Project"
py .\Prototype\scripts\start_kafka.py

```

Leave this terminal running; it remains attached to the database consumer.
Start the sensor in another terminal using the command in **Start the Sensor**.

Check the containers:

```powershell
docker compose --env-file Prototype/.env ps
```

Follow Kafka logs if needed:

```powershell
docker compose --env-file Prototype/.env logs -f kafka
```

Verify that Kafka is reachable from Windows:

```powershell

Test-NetConnection 127.0.0.1 -Port 9092

```

The result should contain:

```text

TcpTestSucceeded : True

```

Open Kafka UI at:

```text
http://localhost:8081
```

The script waits for Kafka before creating `sensor-telemetry`. The Python
bridge subscribes to `sensors/telemetry` and forwards the original payload to
that Kafka topic.

Check the running services:

```powershell
docker compose --env-file Prototype/.env ps
```

Follow bridge logs to verify it subscribed and is forwarding messages:

```powershell
docker compose --env-file Prototype/.env logs -f mqtt-kafka-bridge
```

## MQTT Subscriber (Optional)
Mosquitto is started automatically by `start_kafka.py`, so it does not need to be started manually.

To monitor the MQTT sensor messages in a separate terminal, run:

```powershell

& "C:\Program Files\mosquitto\mosquitto_sub.exe" `

 -h localhost `

 -p 1883 `

 -t sensors/telemetry `

 -v

```

## Start the Sensor
```powershell

Set-Location "C:\Devops_Group_Project"

py .\Prototype\Data_Sensor.py

```

The sensor publishes to `localhost:1883`, which Compose publishes from the
Docker Mosquitto container to Windows.

## View Data in Kafka UI

1. Open `http://localhost:8081`.
2. Select the `local` cluster.

3. Open the `sensor-telemetry` topic.

4. Select the `Messages` tab.

5. Set the value format to `String` or `UTF-8`.

6. Refresh the messages.

The topic should contain the JSON sensor records.

## Stop the Setup
Stop the Windows processes with `Ctrl+C`, then stop Docker services:

```powershell
docker compose --env-file Prototype/.env down
```

This stops containers but preserves the PostgreSQL volume and its data. Do
not use `docker compose --env-file Prototype/.env down -v` unless you
intentionally want to delete the database volume and stored Kafka data.

## Previous Setup Scope (Historical)

The current Compose file runs PostgreSQL, Kafka, Kafka UI, the Python
MQTT-to-Kafka bridge, Mosquitto, Grafana, and the IoT control components in
Docker. The Windows database consumer connects to PostgreSQL using
`Prototype/.env`.

## Dockerised IoT Control System — 21/10/26 updated

### Overview

The IoT control components have been containerised using Docker Compose. The system reads sensor data from a CSV file, publishes readings through MQTT, evaluates configurable control rules and sends commands to an actuator simulator.

The relevant services are:

- `mosquitto` — MQTT broker
- `sensor-simulator` — publishes CSV sensor readings
- `control-logic` — processes sensor readings and applies PostgreSQL control settings
- `actuator-simulator` — receives and simulates actuator commands

### MQTT Topics

| Topic | Purpose |
|---|---|
| `sensors/telemetry` | Sensor readings published by the Sensor Simulator |
| `actuators/commands` | Commands published by Control Logic |

All three Python services connect to the Docker MQTT broker using `mosquitto:1883`.

### Starting the Containers

Open PowerShell in the project root directory.

Ensure Docker Desktop is running. Compose initializes the telemetry database
and the combined control/authentication `control_settings_db` on the same
PostgreSQL server.

Create `Prototype/.env` from the repository's `.env.example`. Set private
values for `DB_PASSWORD` and `AUTH_SECRET_KEY`. The control and authentication
database names should both be `control_settings_db`, with the same PostgreSQL
user and password:

```dotenv
DB_HOST=localhost
DB_PORT=5434
DB_NAME=postgres
DB_USER=postgres
DB_PASSWORD=choose_a_private_password
CONTROL_DB_HOST=localhost
CONTROL_DB_PORT=5434
CONTROL_DB_NAME=control_settings_db
CONTROL_DB_USER=postgres
CONTROL_DB_PASSWORD=choose_a_private_password
AUTH_DB_HOST=localhost
AUTH_DB_PORT=5434
AUTH_DB_NAME=control_settings_db
AUTH_DB_USER=postgres
AUTH_DB_PASSWORD=choose_a_private_password
AUTH_SECRET_KEY=replace_with_a_secure_random_secret
```

Do not commit `.env` files or database passwords to Git. Set any Grafana or
Control Logic-specific variables needed by your local setup in this file as
well. Use `--env-file Prototype/.env` with Compose commands so all services
receive the same values.

Build and start the four IoT services:

```powershell
docker compose --env-file Prototype/.env up -d --build mosquitto control-logic actuator-simulator
```

Start or replay the Sensor Simulator:

```powershell
docker compose --env-file Prototype/.env up -d --force-recreate sensor-simulator
```

Check container status:

```powershell
docker compose --env-file Prototype/.env ps
```

### PostgreSQL Configuration

The telemetry API and Kafka consumer connect to the Compose PostgreSQL
service through `localhost:5434` from Windows. The Dockerized Control Logic
connects to the PostgreSQL server by the Compose hostname `postgres` on port
5432. Its control/authentication database is `control_settings_db`.

The Docker Compose configuration uses:

| Variable | Current value |
|---|---|
| `DB_HOST` | `postgres` inside Docker; `localhost` on Windows |
| `DB_PORT` | `5432` inside Docker; `5434` on Windows |
| `DB_NAME` | `postgres` by default |
| `CONTROL_DB_HOST` | `postgres` inside Docker; `localhost` on Windows |
| `CONTROL_DB_PORT` | `5432` inside Docker; `5434` on Windows |
| `CONTROL_DB_NAME` | `control_settings_db` by default |
| `AUTH_DB_NAME` | Same as `CONTROL_DB_NAME` |

`database-init` creates and initializes `control_settings_db` on the Compose
PostgreSQL server. The Compose API and Control Logic services use the internal
Docker hostname; local Windows processes use the published host port.

Control settings are retrieved from the `control_settings` table, including:

- `temperature_threshold`
- `humidity_threshold`
- `light_enabled`

The Control Logic uses these saved values to determine which actuator commands to publish.

### Testing the Sensor-to-Actuator Flow

Check that the Sensor Simulator publishes CSV readings:

```powershell
docker compose --env-file Prototype/.env logs --tail=50 sensor-simulator
```

Check that Control Logic receives sensor readings and publishes commands:

```powershell
docker compose --env-file Prototype/.env logs --tail=100 control-logic
```

Check that the Actuator Simulator receives commands:

```powershell
docker compose --env-file Prototype/.env logs --tail=50 actuator-simulator
```

The expected flow is:

```text
Data_Sensor.py
    |
    v
Mosquitto MQTT (sensors/telemetry)
    |
    v
Control_Logic.py
    |
    +-- PostgreSQL control settings
    |
    v
Mosquitto MQTT (actuators/commands)
    |
    v
Actuator_Simulator.py
```

### Testing Completed

The following tests were completed during SCRUM-102:

- All four IoT components started successfully using Docker Compose.
- The Sensor Simulator published 10 readings from the IoT CSV dataset.
- Control Logic received live MQTT sensor messages.
- Control Logic successfully retrieved PostgreSQL settings.
- Readings exceeding the configured humidity threshold generated Dehumidifier ON commands.
- The Actuator Simulator received and simulated the commands.
- A separate below-threshold test generated no actuator commands.

### Group Handover Notes

The IoT control components have been containerised and tested together.

Before the full group deployment, the following integration points should be reviewed:

1. Confirm that `database-init` completes successfully and both applications
   connect to the initialized `control_settings_db`.
2. Verify that the Python bridge forwards sensor messages from MQTT to Kafka.
3. Confirm that the bridge works on the target operating system without a
   host-specific Kafka plugin path.
4. Confirm that all services start correctly using the local
   `Prototype/.env`.
5. Retest the complete sensor, Kafka, telemetry database, control and
   actuator flow after starting the merged Compose stack.

### Stopping the Services

Stop the IoT components without removing the rest of the group's running services:

```powershell
docker compose --env-file Prototype/.env stop sensor-simulator control-logic actuator-simulator mosquitto
```

The MQTT broker currently allows anonymous connections for local development. Authentication and appropriate access controls should be added before production deployment.

## Control API

The Control API runs as a Docker Compose service alongside the other project components. It provides API endpoints for accessing and managing the control system.

### Prerequisites

- Docker Desktop is installed and running.
- The project repository has been cloned.
- The required environment variables and database settings are configured in the project's local `.env` file.

Do not commit passwords or other secrets to Git.

### Start the Control API

Run these commands from the project root:

```powershell
docker compose --env-file Prototype/.env config --quiet
docker compose --env-file Prototype/.env up -d --build control-api
```

Check the service status:

```powershell
docker compose --env-file Prototype/.env ps control-api
```

View the API logs if needed:

```powershell
docker compose --env-file Prototype/.env logs --tail=50 control-api
```

### Access the API

Once the service is running, open the interactive API documentation:

`http://localhost:8000/docs`

### Stop the Control API

To stop only the Control API:

```powershell
docker compose --env-file Prototype/.env stop control-api
```

To rebuild and restart it after code changes:

```powershell
docker compose --env-file Prototype/.env up -d --build control-api
```

### Troubleshooting

- If the container does not start, check the logs using `docker compose --env-file Prototype/.env logs control-api`.
- If port 8000 is already in use, check for another service using that port.
- If the API cannot connect to the database, check the `.env` settings and confirm that the database service or configured database host is reachable.
- If the Compose configuration is invalid, run `docker compose --env-file Prototype/.env config` to display the resolved configuration and look for errors.

## One-command local CI and Compose run

From the repository root in PowerShell, run:

```powershell
.\run-local-ci.ps1
```

The script runs the same Python tests as GitHub Actions plus a building API
import smoke test, builds the API, Control Logic, Sensor Simulator, and
Actuator Simulator images, and starts the Docker Compose stack using the
current checkout. It then waits up to three minutes for
`GET /telemetry/?limit=1` to verify the API and database connection. Compose
health checks get up to three additional minutes to finish or recover; if any
remain unhealthy, the script prints service logs and health details. PostgreSQL
must be out of recovery before initialization starts, and the idempotent
database initialization retries transient failures up to three times.

The full run requires Docker Desktop, Python 3.12, `Prototype/.env`, and
`curl.exe`. The script
creates or repairs the repository `.venv` when needed. Do not commit
`Prototype/.env` or include its secret values in logs or screenshots.

To run the CI tests and build all five images without starting Compose:

```powershell
.\run-local-ci.ps1 -BuildOnly
```

The Compose services remain running after the script exits. Stop the stack
without deleting its named data volumes by running:

```powershell
docker compose --env-file Prototype/.env down
```

This script validates the local checkout and Compose application. It does not
deploy through Argo CD, publish images to GHCR, or push Git commits. GitHub's
image publishing and GitOps update jobs run only for the configured
main-branch workflow. For Argo CD setup and deployment verification, see the
following **GitOps Deployment Management with Argo CD** section.

## GitOps Deployment Management with Argo CD

### Goal and deployment flow

The deployment issue being addressed is that Argo CD repository synchronization
has been demonstrated, but a healthy end-to-end Kubernetes deployment has not
yet been verified. Earlier checks showed image-pull and application dependency
problems. This work configures Argo CD to follow Git, automates container
publishing and manifest updates, and verifies that the application reaches a
healthy state.

On a push to `main`, GitHub Actions runs the checks, builds the application
images, publishes commit-SHA tags to GHCR, and updates the API and control-logic
image references in the Kubernetes manifests. It then pushes a GitOps commit.
Argo CD watches the `k8s` path on `main`, detects that commit, and reconciles the
manifests to the cluster. Automatic sync applies the desired state; self-heal
corrects manual drift; pruning removes resources deleted from Git. GitHub
Actions does not need Kubernetes credentials.

**Branch behavior:** Each teammate can work on `<branch name>`, but the image
publishing and GitOps update jobs only run on `main`. Replace the placeholder
with the actual remote branch name, without angle brackets, when testing a
feature branch in a personal/local cluster. To test the full CI-to-deployment
flow, merge reviewed changes to `main` through the team's pull-request process.
Do not commit a personal branch name as the production Argo CD target revision.

The Application manifest is `k8s/argocd/application.yaml`. It targets `main`
and the `k8s` path. Main-branch workload namespaces can differ from feature
branch namespaces; use the namespace declared in the manifests being tested.
The local feature-branch test may change only the live Application in that
local cluster.

### Prerequisites

- Docker Desktop and kind, or another Kubernetes cluster, with a working
  `kubectl` context.
- Argo CD installed in the cluster and repository access configured. Public
  repositories do not need credentials; for a private repository configure a
  read-only Git credential in Argo CD, not in Git.
- Required runtime secrets and dependencies for the workloads in the selected
  manifests. The Compose services described in this file do not automatically
  become services in Kubernetes.
- GitHub Actions workflow-token write permission and branch rules that permit
  its GitOps commit to `main`. If policy disallows bot pushes, the workflow
  needs to create a reviewed pull request instead.

### Subtask 1 — Provision local Kubernetes and Argo CD

Create the cluster only if it does not already exist. Check the context before
installing Argo CD so it goes into the intended cluster:

```powershell
kind get clusters
# Run only if iot-gitops is not listed:
kind create cluster --name iot-gitops
kubectl config use-context kind-iot-gitops
kubectl config current-context
kubectl create namespace argocd --dry-run=client -o yaml | kubectl apply -f -
kubectl apply -n argocd -f https://raw.githubusercontent.com/argoproj/argo-cd/stable/manifests/install.yaml
kubectl wait --for=condition=Available deployment/argocd-server -n argocd --timeout=300s
kubectl wait --for=condition=Available deployment/argocd-repo-server -n argocd --timeout=300s
kubectl get nodes -o wide
kubectl get pods -n argocd -o wide
```

**Expected:** The context is `kind-iot-gitops`, the node is Ready, and Argo CD
pods are Running with their containers ready. **Evidence:** Save the context,
node, and Argo CD pod output. **Recorded status:** The local kind cluster and
Argo CD pods were reported ready.

### Subtask 2 — Configure the Application and repository access

Apply the committed Application, which tracks `main`, then refresh and inspect
the resource state:

```powershell
kubectl apply -f k8s\argocd\application.yaml
kubectl annotate application iot-app -n argocd argocd.argoproj.io/refresh=hard --overwrite
kubectl get application iot-app -n argocd -o wide
kubectl describe application iot-app -n argocd
```

For local feature-branch testing, the branch must already exist remotely and
the desired changes must be pushed. Enter its name without the angle brackets:

```powershell
$branch = Read-Host "Enter <branch name>"
git ls-remote --heads origin $branch
```

If Git lists the branch, run `kubectl edit application iot-app -n argocd`,
change `spec.source.targetRevision` to the actual `<branch name>` (without
angle brackets), and save. Then refresh and inspect:

```powershell
kubectl annotate application iot-app -n argocd argocd.argoproj.io/refresh=hard --overwrite
kubectl get application iot-app -n argocd -o wide
kubectl describe application iot-app -n argocd
```

After feature-branch testing, edit the local Application's
`spec.source.targetRevision` back to `main` and refresh again. Branch changes
apply only to the local cluster. Because pruning is enabled, changing branches
can delete resources that are present only in the previous branch; check the
manifests before switching.

**Expected:** Argo CD can read and render the selected Git revision and reports
its sync status, health, revision, and resources. **Evidence:** Application
page or command output. **Recorded status:** Repository access and sync were
previously demonstrated on a feature branch; the observed inventory then
contained only the `iot-app` Namespace. Full workload health on `main` remains
to be verified.

Open the Argo CD UI in one PowerShell window:

```powershell
kubectl port-forward svc/argocd-server -n argocd 8080:443
```

Then open `https://localhost:8080`. If the initial admin password is still
available, retrieve it locally (do not include it in screenshots or Jira):

```powershell
$encodedPassword = kubectl -n argocd get secret argocd-initial-admin-secret -o jsonpath="{.data.password}"
[Text.Encoding]::UTF8.GetString([Convert]::FromBase64String($encodedPassword))
```

Before syncing workloads, create the runtime Secrets required by the selected
manifests in their target namespace. Keep credentials out of Git and avoid
including secret values in saved terminal output.

### Subtask 3 — Automate image publishing and GitOps updates

This main-only automation is not tested by pushing to `<branch name>`. After
the reviewed changes reach `main`, list recent workflow runs and inspect the
run associated with the merged change:

```powershell
gh run list --workflow ci.yml --branch main --limit 5
$runId = Read-Host "Enter the Actions run ID"
gh run view $runId
gh run view $runId --log
```

Confirm the Python checks, image builds, and **Update GitOps image tags** job
succeeded. Then verify that the API and control-logic image references in the
latest `main` contain the built commit SHA:

```powershell
$sha = gh run view $runId --json headSha --jq .headSha
git fetch origin main
git show origin/main:k8s/control-api.yaml | Select-String "image:.*$sha"
git show origin/main:k8s/control-logic.yaml | Select-String "image:.*$sha"
git log -1 --oneline origin/main
```

**Expected:** GHCR images are published with the source commit SHA, both
manifest references are updated, and `main` contains the GitOps update commit.
If the updater cannot push, check Actions token permissions and branch rules.
**Evidence:** Successful Actions run, updated image references, and GitOps
commit. **Recorded status:** A successful main-branch publishing and update
run has not yet been evidenced.

### Subtask 4 — Validate deployment health and visibility

Check the Application, resources, and rollout status. Substitute the workload
namespace if it differs from `devops` in the manifests being tested:

```powershell
kubectl get application iot-app -n argocd -o wide
kubectl describe application iot-app -n argocd
kubectl get deployments,pods,services -n devops
kubectl rollout status deployment/control-api -n devops --timeout=180s
kubectl rollout status deployment/control-logic -n devops --timeout=180s
```

If a pod is unhealthy, inspect its events:

```powershell
kubectl get pods -n devops
$pod = Read-Host "Enter the unhealthy pod name"
kubectl describe pod $pod -n devops
```

Forward the API in one terminal and request its endpoint from another:

```powershell
kubectl port-forward service/control-api -n devops 8000:8000
```

```powershell
Invoke-WebRequest http://localhost:8000/telemetry/
```

**Expected:** Argo CD reports `Synced` and `Healthy`, both rollouts complete,
and the endpoint returns successfully. `ImagePullBackOff` indicates image
availability or pull access still needs attention; missing dependencies or
secrets can also prevent readiness. **Evidence:** Application status, rollout
output, and API response. **Recorded status:** Workload health and the API
response are still pending successful runtime checks.

### Jira-ready summary

**Title:** Implement and verify GitOps deployments with Argo CD

**Description:** Argo CD repository synchronization has been demonstrated, but
the application has not yet passed end-to-end deployment health checks. The
work configures a local Kubernetes/Argo CD environment, connects the
Application to Git, automates GHCR image publishing and manifest updates on
`main`, and verifies workload health and API availability. Feature branches
can be tested locally using `<branch name>`, but only a reviewed merge to
`main` activates the complete image-publishing and GitOps workflow.

**Acceptance:** A successful main-branch workflow publishes images and updates
their manifest references; Argo CD reconciles the GitOps commit; required
workloads become healthy; and the API responds. Capture command output or
screenshots for each completed subtask. Never include tokens, passwords,
kubeconfig contents, or secret values in Jira.
