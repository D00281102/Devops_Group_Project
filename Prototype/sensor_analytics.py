import csv
from datetime import datetime

DATA_FILE = "Prototype/data/iot_telemetry_data.csv"


def analyse_sensor_data(rows):

    temperatures = []
    humidities = []
    co_readings = []

    device_data = {}
    daily_data = {}

    for row in rows:
        temperature = float(row["temp"])
        humidity = float(row["humidity"])
        co = float(row["co"])
        device = row["device"]
        timestamp = float(row["ts"])

        temperatures.append(temperature)
        humidities.append(humidity)
        co_readings.append(co)

        # Per-device analytics
        if device not in device_data:
            device_data[device] = {
                "temperatures": [],
                "humidities": []
            }

        device_data[device]["temperatures"].append(temperature)
        device_data[device]["humidities"].append(humidity)

        # Daily trends
        date = datetime.fromtimestamp(timestamp).date()

        if date not in daily_data:
            daily_data[date] = {
                "temperatures": [],
                "humidities": []
            }

        daily_data[date]["temperatures"].append(temperature)
        daily_data[date]["humidities"].append(humidity)


    # Temperature analytics
    print("Temperature Analytics")
    print("---------------------")
    print(f"Number of readings: {len(temperatures)}")
    print(f"Average temperature: {sum(temperatures)/len(temperatures):.2f} °C")
    print(f"Minimum temperature: {min(temperatures):.2f} °C")
    print(f"Maximum temperature: {max(temperatures):.2f} °C")

    print()

    # Humidity analytics
    print("Humidity Analytics")
    print("------------------")
    print(f"Number of readings: {len(humidities)}")
    print(f"Average humidity: {sum(humidities)/len(humidities):.2f} %")
    print(f"Minimum humidity: {min(humidities):.2f} %")
    print(f"Maximum humidity: {max(humidities):.2f} %")

    print()

    # CO analytics
    print("CO Analytics")
    print("------------")
    print(f"Number of readings: {len(co_readings)}")
    print(f"Average CO: {sum(co_readings)/len(co_readings):.6f}")
    print(f"Minimum CO: {min(co_readings):.6f}")
    print(f"Maximum CO: {max(co_readings):.6f}")

    print()

    # Device analytics
    print("Per-Device Analytics")
    print("--------------------")

    for device, readings in device_data.items():

        temps = readings["temperatures"]
        humidity_values = readings["humidities"]

        print(f"Device: {device}")
        print(f"Readings: {len(temps)}")
        print(f"Average temperature: {sum(temps)/len(temps):.2f} °C")
        print(f"Average humidity: {sum(humidity_values)/len(humidity_values):.2f} %")
        print()


    # Daily trends
    print("Daily Sensor Trends")
    print("-------------------")

    for date in sorted(daily_data):

        temps = daily_data[date]["temperatures"]
        humidity_values = daily_data[date]["humidities"]

        print(f"Date: {date}")
        print(f"Readings: {len(temps)}")
        print(f"Average temperature: {sum(temps)/len(temps):.2f} °C")
        print(f"Average humidity: {sum(humidity_values)/len(humidity_values):.2f} %")
        print()


# Current CSV input for testing
with open(DATA_FILE, "r", newline="") as file:

    reader = csv.DictReader(file)

    analyse_sensor_data(reader)