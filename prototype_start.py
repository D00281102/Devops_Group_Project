from pathlib import Path
import shutil
import subprocess
import sys


PROJECT_ROOT = Path(__file__).resolve().parent
COMPOSE_FILE = PROJECT_ROOT / "docker-compose.yml"
ENV_FILE = PROJECT_ROOT / "Prototype" / ".env"
SCRIPTS_DIR = PROJECT_ROOT / "Prototype" / "scripts"
START_MQTT_SCRIPT = SCRIPTS_DIR / "start_mqtt.py"
START_KAFKA_SCRIPT = SCRIPTS_DIR / "start_kafka.py"


def main():
    if not COMPOSE_FILE.is_file():
        raise FileNotFoundError(f"docker-compose.yml was not found in {PROJECT_ROOT}.")

    if not ENV_FILE.is_file():
        raise FileNotFoundError(
            "Prototype/.env was not found. Create it from .env.example before starting."
        )

    if shutil.which("docker") is None:
        raise RuntimeError(
            "Docker was not found on PATH. Install Docker Desktop and try again."
        )

    for script in (START_MQTT_SCRIPT, START_KAFKA_SCRIPT):
        if not script.is_file():
            raise FileNotFoundError(f"Startup script was not found: {script}")

    compose_base_command = [
        "docker",
        "compose",
        "--env-file",
        str(ENV_FILE),
    ]
    subprocess.run(
        [*compose_base_command, "config", "--quiet"],
        cwd=PROJECT_ROOT,
        check=True,
    )

    python_executable = sys.executable
    startup_processes = []
    print("Starting the MQTT and Kafka scripts...")
    try:
        subprocess.run(
            [python_executable, str(START_MQTT_SCRIPT)],
            cwd=SCRIPTS_DIR,
            check=True,
        )

        subprocess.run(
            [*compose_base_command, "up", "-d", "--build"],
            cwd=PROJECT_ROOT,
            check=True,
        )

        startup_processes.append(
            subprocess.Popen(
                [python_executable, str(START_KAFKA_SCRIPT)],
                cwd=SCRIPTS_DIR,
            )
        )

        print("\nPrototype services:")
        subprocess.run(
            [*compose_base_command, "ps"],
            cwd=PROJECT_ROOT,
            check=True,
        )
    except (OSError, subprocess.CalledProcessError):
        for process in startup_processes:
            if process.poll() is None:
                process.terminate()
        raise


if __name__ == "__main__":
    try:
        main()
    except (FileNotFoundError, RuntimeError, subprocess.CalledProcessError) as error:
        print(f"ERROR: {error}", file=sys.stderr)
        sys.exit(1)
