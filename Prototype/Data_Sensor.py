import csv
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
            print(f"{row_number}: {row}")

            if row_number == 5:
                break


if __name__ == "__main__":
    display_sensor_data()