[CmdletBinding()]
param(
    [switch]$BuildOnly
)

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

$repositoryRoot = $PSScriptRoot
$prototypeDirectory = Join-Path $repositoryRoot "Prototype"
$venvPython = Join-Path $repositoryRoot ".venv\Scripts\python.exe"
$envFile = Join-Path $prototypeDirectory ".env"
function Invoke-CheckedCommand {
    param(
        [Parameter(Mandatory = $true)]
        [string]$FilePath,

        [Parameter(Mandatory = $true)]
        [string[]]$Arguments,

        [Parameter(Mandatory = $true)]
        [string]$Description
    )

    & $FilePath @Arguments
    if ($LASTEXITCODE -ne 0) {
        throw "$Description failed with exit code $LASTEXITCODE."
    }
}

if (Test-Path -LiteralPath $venvPython) {
    $pythonVersion = & $venvPython --version
    if ($LASTEXITCODE -ne 0) {
        $pythonVersion = "could not be determined"
    }
}
else {
    $pythonVersion = $null
}

if ($pythonVersion -notmatch "^Python 3\.12(\.|$)") {
    if (-not (Get-Command py.exe -ErrorAction SilentlyContinue)) {
        throw "Python 3.12 launcher was not found. Install Python 3.12, then rerun this script."
    }

    $launcherVersion = & py.exe -3.12 --version
    if ($LASTEXITCODE -ne 0 -or $launcherVersion -notmatch "^Python 3\.12(\.|$)") {
        throw "Python 3.12 is not available through the Python launcher. Install Python 3.12, then rerun this script."
    }

    Invoke-CheckedCommand -FilePath "py.exe" `
        -Arguments @("-3.12", "-m", "venv", "--clear", (Join-Path $repositoryRoot ".venv")) `
        -Description "Create the local Python 3.12 environment"
}

$pythonVersion = & $venvPython --version
if ($LASTEXITCODE -ne 0 -or $pythonVersion -notmatch "^Python 3\.12(\.|$)") {
    throw "The repository .venv must use Python 3.12 to match GitHub Actions. Current version: $pythonVersion"
}

if (-not (Get-Command docker.exe -ErrorAction SilentlyContinue)) {
    throw "Docker CLI was not found. Install/start Docker Desktop, then rerun this script."
}

Invoke-CheckedCommand -FilePath "docker.exe" `
    -Arguments @("info", "--format", "{{.ServerVersion}}") `
    -Description "Check the Docker daemon"

if (-not $BuildOnly) {
    if (-not (Test-Path -LiteralPath $envFile)) {
        throw "Missing $envFile. Create Prototype\.env with the required local secrets before starting Compose."
    }
    if (-not (Get-Command curl.exe -ErrorAction SilentlyContinue)) {
        throw "curl.exe is required to verify the API after Compose starts."
    }

    Invoke-CheckedCommand -FilePath "docker.exe" `
        -Arguments @("compose", "--env-file", $envFile, "config", "--quiet") `
        -Description "Validate the Docker Compose configuration"
}

$ciEnvironment = [ordered]@{
    DB_HOST             = "127.0.0.1"
    DB_PORT             = "1"
    DB_NAME             = "postgres"
    DB_USER             = "postgres"
    DB_PASSWORD         = "ci-only-placeholder"
    CONTROL_DB_PASSWORD = "ci-only-placeholder"
    AUTH_DB_PASSWORD    = "ci-only-placeholder"
    AUTH_SECRET_KEY     = "ci-only-placeholder"
}
$previousEnvironment = @{}
$locationPushed = $false

try {
    foreach ($name in $ciEnvironment.Keys) {
        $previousEnvironment[$name] = [Environment]::GetEnvironmentVariable($name, "Process")
        [Environment]::SetEnvironmentVariable($name, $ciEnvironment[$name], "Process")
    }

    Push-Location $prototypeDirectory
    $locationPushed = $true

    Invoke-CheckedCommand -FilePath $venvPython `
        -Arguments @("-m", "pip", "install", "--upgrade", "pip") `
        -Description "Upgrade pip"
    Invoke-CheckedCommand -FilePath $venvPython `
        -Arguments @("-m", "pip", "install", "-r", "requirements.txt") `
        -Description "Install CI Python dependencies"
    Invoke-CheckedCommand -FilePath $venvPython `
        -Arguments @("test_sensor_analytics.py") `
        -Description "Run sensor analytics tests"
    Invoke-CheckedCommand -FilePath $venvPython `
        -Arguments @("test_control_logic.py") `
        -Description "Run control logic tests"
    Invoke-CheckedCommand -FilePath $venvPython `
        -Arguments @("test_start_kafka.py") `
        -Description "Run Kafka startup tests"
    Invoke-CheckedCommand -FilePath $venvPython `
        -Arguments @("test_mqtt_kafka_bridge.py") `
        -Description "Run MQTT-to-Kafka bridge tests"
    Invoke-CheckedCommand -FilePath $venvPython `
        -Arguments @("-c", "import api.buildings") `
        -Description "Smoke-test the building API imports"
}
finally {
    if ($locationPushed) {
        Pop-Location
    }
    foreach ($name in $ciEnvironment.Keys) {
        [Environment]::SetEnvironmentVariable($name, $previousEnvironment[$name], "Process")
    }
}

$images = @(
    @{ Dockerfile = "Dockerfile.api"; Tag = "iot-control-api:latest" },
    @{ Dockerfile = "Dockerfile.control"; Tag = "iot-control-logic:latest" },
    @{ Dockerfile = "Dockerfile.sensor"; Tag = "iot-sensor-simulator:latest" },
    @{ Dockerfile = "Dockerfile.actuator"; Tag = "iot-actuator-simulator:latest" },
    @{ Dockerfile = "Dockerfile.mqtt-kafka"; Tag = "iot-mqtt-kafka-bridge:latest" }
)

foreach ($image in $images) {
    $dockerfilePath = Join-Path $prototypeDirectory $image.Dockerfile
    Invoke-CheckedCommand -FilePath "docker.exe" `
        -Arguments @("build", "--file", $dockerfilePath, "--tag", $image.Tag, $prototypeDirectory) `
        -Description "Build $($image.Tag)"
}

if ($BuildOnly) {
    Write-Host "CI checks passed and all five local images were built. Compose services were not started."
    return
}

Invoke-CheckedCommand -FilePath "docker.exe" `
    -Arguments @("compose", "--env-file", $envFile, "up", "--detach", "--no-build", "--remove-orphans") `
    -Description "Start the Docker Compose stack"

$apiUrl = "http://localhost:8000/telemetry/?limit=1"
$apiReady = $false
$deadline = (Get-Date).AddMinutes(3)
Write-Host "Waiting for the API telemetry/database check at $apiUrl ..."

while ((Get-Date) -lt $deadline) {
    & curl.exe --fail --silent --max-time 5 --output NUL $apiUrl
    if ($LASTEXITCODE -eq 0) {
        $apiReady = $true
        break
    }

    Start-Sleep -Seconds 5
}

if (-not $apiReady) {
    Write-Warning "The API did not pass its telemetry/database check within three minutes. Compose status and relevant logs follow."
    & docker.exe compose --env-file $envFile ps
    if ($LASTEXITCODE -ne 0) {
        Write-Warning "Could not retrieve Docker Compose service status."
    }
    & docker.exe compose --env-file $envFile logs --tail=60 postgres database-init control-api kafka mqtt-kafka-bridge
    if ($LASTEXITCODE -ne 0) {
        Write-Warning "Could not retrieve one or more service logs."
    }
    throw "Local CI tests and image builds completed, but the Compose API/DB smoke test failed."
}

$healthCheckDeadline = (Get-Date).AddMinutes(3)
$composeStatus = @()
$pendingHealthChecks = @()
do {
    $composeStatus = & docker.exe compose --env-file $envFile ps
    if ($LASTEXITCODE -ne 0) {
        throw "Show Docker Compose service status failed with exit code $LASTEXITCODE."
    }

    $pendingHealthChecks = @(
        $composeStatus | Select-String -Pattern "\((?:unhealthy|health:\s*starting)\)"
    )
    if ($pendingHealthChecks.Count -eq 0 -or (Get-Date) -ge $healthCheckDeadline) {
        break
    }

    Write-Host "Waiting for Compose health checks to recover or finish starting ..."
    Start-Sleep -Seconds 5
} while ($true)

Write-Host ($composeStatus -join [Environment]::NewLine)

if ($pendingHealthChecks.Count -gt 0) {
    Write-Warning "Compose health checks did not all become healthy within three minutes. Recent service logs and health details follow."
    & docker.exe compose --env-file $envFile logs --tail=60
    if ($LASTEXITCODE -ne 0) {
        Write-Warning "Could not retrieve Docker Compose service logs."
    }

    $containerIds = & docker.exe compose --env-file $envFile ps --quiet
    if ($LASTEXITCODE -eq 0) {
        foreach ($containerId in $containerIds) {
            & docker.exe inspect --format "{{.Name}} {{if .State.Health}}health={{.State.Health.Status}} details={{json .State.Health.Log}}{{else}}health=not-configured{{end}}" $containerId
        }
    }
    else {
        Write-Warning "Could not retrieve Docker Compose container health details."
    }
    throw "The API/DB check passed, but Compose health checks did not all become healthy."
}

Write-Host "CI checks passed, all five images were built, the API/database check succeeded, and no Compose service reports unhealthy."
Write-Host "API docs: http://localhost:8000/docs"
Write-Host "Kafka UI: http://localhost:8081"
Write-Host "Grafana:  http://localhost:3001"
