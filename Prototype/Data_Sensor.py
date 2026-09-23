import csv
import json
from pathlib import Path

# Path to the IoT telemetry dataset
DATA_FILE = Path(__file__).parent / "data" / "iot_telemetry_data.csv"


def display_sensor_data():
    """
    Read the sensor dataset and display sample readings.
    """

    with open(DATA_FILE, "r", newline="", encoding="utf-8") as file:
        reader = csv.DictReader(file)

        print("Dataset columns:")
        print(reader.fieldnames)

        print("\nFirst 5 sensor readings:")

        for row_number, row in enumerate(reader, start=1):
            sensor_message = {
                "ts": float(row["ts"]),
                "device": row["device"],
                "co": float(row["co"]),
                "humidity": float(row["humidity"]),
                "light": row["light"].lower() == "true",
                "lpg": float(row["lpg"]),
                "motion": row["motion"].lower() == "true",
                "smoke": float(row["smoke"]),
                "temp": float(row["temp"])
            }

            print(json.dumps(sensor_message, indent=4))

            if row_number == 5:
                break


if __name__ == "__main__":
    display_sensor_data()