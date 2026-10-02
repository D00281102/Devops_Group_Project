from pathlib import Path
import socket
import subprocess
import time


MOSQUITTO_PATH = r"C:\Program Files\mosquitto\mosquitto.exe"
MOSQUITTO_CONFIG = Path(__file__).resolve().parents[1] / "mosquitto.conf"
MQTT_HOST = "localhost"
MQTT_PORT = 1883


def mqtt_is_running():
    """Check whether an MQTT broker is already listening on port 1883."""
    try:
        with socket.create_connection((MQTT_HOST, MQTT_PORT), timeout=2):
            return True
    except OSError:
        return False


def start_mqtt():
    """Start the local Mosquitto MQTT broker if it is not already running."""

    if mqtt_is_running():
        print("Mosquitto MQTT broker is already running.")
        return None

    print("Starting Mosquitto MQTT broker...")

    process = subprocess.Popen([
        MOSQUITTO_PATH,
        "-c",
        str(MOSQUITTO_CONFIG),
        "-v"
    ])

    for attempt in range(10):
        if mqtt_is_running():
            print("Mosquitto MQTT broker is ready on localhost:1883.")
            return process

        print(f"Waiting for Mosquitto... ({attempt + 1}/10)")
        time.sleep(1)

    process.terminate()
    raise RuntimeError("Mosquitto MQTT broker did not become ready.")


if __name__ == "__main__":
    start_mqtt()