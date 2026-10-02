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

    if not temperatures:
        return {
            "temperature": {},
            "humidity": {},
            "co": {},
            "devices": {},
            "daily_trends": {}
        }

    results = {
        "temperature": {
            "count": len(temperatures),
            "average": sum(temperatures) / len(temperatures),
            "minimum": min(temperatures),
            "maximum": max(temperatures)
        },
        "humidity": {
            "count": len(humidities),
            "average": sum(humidities) / len(humidities),
            "minimum": min(humidities),
            "maximum": max(humidities)
        },
        "co": {
            "count": len(co_readings),
            "average": sum(co_readings) / len(co_readings),
            "minimum": min(co_readings),
            "maximum": max(co_readings)
        },
        "devices": {},
        "daily_trends": {}
    }

    # Per-device results
    for device, readings in device_data.items():
        temps = readings["temperatures"]
        humidity_values = readings["humidities"]

        results["devices"][device] = {
            "readings": len(temps),
            "average_temperature": sum(temps) / len(temps),
            "average_humidity": sum(humidity_values) / len(humidity_values)
        }

    # Daily trend results
    for date in sorted(daily_data):
        temps = daily_data[date]["temperatures"]
        humidity_values = daily_data[date]["humidities"]

        results["daily_trends"][str(date)] = {
            "readings": len(temps),
            "average_temperature": sum(temps) / len(temps),
            "average_humidity": sum(humidity_values) / len(humidity_values)
        }

    print_analytics(results)

    return results


def print_analytics(results):
    temperature = results["temperature"]
    humidity = results["humidity"]
    co = results["co"]

    print("Temperature Analytics")
    print("---------------------")
    print(f"Number of readings: {temperature['count']}")
    print(f"Average temperature: {temperature['average']:.2f} C")
    print(f"Minimum temperature: {temperature['minimum']:.2f} C")
    print(f"Maximum temperature: {temperature['maximum']:.2f} C")

    print()

    print("Humidity Analytics")
    print("------------------")
    print(f"Number of readings: {humidity['count']}")
    print(f"Average humidity: {humidity['average']:.2f} %")
    print(f"Minimum humidity: {humidity['minimum']:.2f} %")
    print(f"Maximum humidity: {humidity['maximum']:.2f} %")

    print()

    print("CO Analytics")
    print("------------")
    print(f"Number of readings: {co['count']}")
    print(f"Average CO: {co['average']:.6f}")
    print(f"Minimum CO: {co['minimum']:.6f}")
    print(f"Maximum CO: {co['maximum']:.6f}")

    print()

    print("Per-Device Analytics")
    print("--------------------")

    for device, data in results["devices"].items():
        print(f"Device: {device}")
        print(f"Readings: {data['readings']}")
        print(f"Average temperature: {data['average_temperature']:.2f} C")
        print(f"Average humidity: {data['average_humidity']:.2f} %")
        print()

    print("Daily Sensor Trends")
    print("-------------------")

    for date, data in results["daily_trends"].items():
        print(f"Date: {date}")
        print(f"Readings: {data['readings']}")
        print(f"Average temperature: {data['average_temperature']:.2f} C")
        print(f"Average humidity: {data['average_humidity']:.2f} %")
        print()


def analyse_csv_file():
    with open(DATA_FILE, "r", newline="", encoding="utf-8") as file:
        reader = csv.DictReader(file)
        return analyse_sensor_data(reader)


if __name__ == "__main__":
    analyse_csv_file()