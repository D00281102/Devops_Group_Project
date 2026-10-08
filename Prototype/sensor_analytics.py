import csv
from datetime import datetime

DATA_FILE = "Prototype/data/iot_telemetry_data.csv"

# Analytics warning thresholds
HIGH_TEMPERATURE = 25.0
LOW_TEMPERATURE = 10.0
HIGH_HUMIDITY = 70.0
LOW_HUMIDITY = 30.0
HIGH_CO = 0.01


def get_status(value, low=None, high=None):
    if high is not None and value > high:
        return "high"

    if low is not None and value < low:
        return "low"

    return "normal"


def analyse_sensor_data(rows):
    temperatures = []
    humidities = []
    co_readings = []

    device_data = {}
    daily_data = {}

    latest_temperature = None
    latest_humidity = None
    latest_co = None

    for row in rows:
        temperature = float(row["temp"])
        humidity = float(row["humidity"])
        co = float(row["co"])
        device = row["device"]
        timestamp = float(row["ts"])

        temperatures.append(temperature)
        humidities.append(humidity)
        co_readings.append(co)

        # Keep the latest reading from the supplied data
        latest_temperature = temperature
        latest_humidity = humidity
        latest_co = co

        if device not in device_data:
            device_data[device] = {
                "temperatures": [],
                "humidities": []
            }

        device_data[device]["temperatures"].append(temperature)
        device_data[device]["humidities"].append(humidity)

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
            "alerts": {},
            "devices": {},
            "daily_trends": {}
        }

    average_temperature = sum(temperatures) / len(temperatures)
    average_humidity = sum(humidities) / len(humidities)
    average_co = sum(co_readings) / len(co_readings)

    results = {
        "temperature": {
            "count": len(temperatures),
            "average": average_temperature,
            "minimum": min(temperatures),
            "maximum": max(temperatures),
            "latest": latest_temperature
        },
        "humidity": {
            "count": len(humidities),
            "average": average_humidity,
            "minimum": min(humidities),
            "maximum": max(humidities),
            "latest": latest_humidity
        },
        "co": {
            "count": len(co_readings),
            "average": average_co,
            "minimum": min(co_readings),
            "maximum": max(co_readings),
            "latest": latest_co
        },
        "alerts": {
            "temperature_status": get_status(
                latest_temperature,
                LOW_TEMPERATURE,
                HIGH_TEMPERATURE
            ),
            "humidity_status": get_status(
                latest_humidity,
                LOW_HUMIDITY,
                HIGH_HUMIDITY
            ),
            "co_status": get_status(
                latest_co,
                high=HIGH_CO
            )
        },
        "devices": {},
        "daily_trends": {}
    }

    for device, readings in device_data.items():
        temps = readings["temperatures"]
        humidity_values = readings["humidities"]

        results["devices"][device] = {
            "readings": len(temps),
            "average_temperature": sum(temps) / len(temps),
            "average_humidity": sum(humidity_values) / len(humidity_values)
        }

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
    alerts = results["alerts"]

    print("Temperature Analytics")
    print("---------------------")
    print(f"Number of readings: {temperature['count']}")
    print(f"Average temperature: {temperature['average']:.2f} C")
    print(f"Minimum temperature: {temperature['minimum']:.2f} C")
    print(f"Maximum temperature: {temperature['maximum']:.2f} C")
    print(f"Latest temperature: {temperature['latest']:.2f} C")
    print(f"Status: {alerts['temperature_status']}")

    print()

    print("Humidity Analytics")
    print("------------------")
    print(f"Number of readings: {humidity['count']}")
    print(f"Average humidity: {humidity['average']:.2f} %")
    print(f"Minimum humidity: {humidity['minimum']:.2f} %")
    print(f"Maximum humidity: {humidity['maximum']:.2f} %")
    print(f"Latest humidity: {humidity['latest']:.2f} %")
    print(f"Status: {alerts['humidity_status']}")

    print()

    print("CO Analytics")
    print("------------")
    print(f"Number of readings: {co['count']}")
    print(f"Average CO: {co['average']:.6f}")
    print(f"Minimum CO: {co['minimum']:.6f}")
    print(f"Maximum CO: {co['maximum']:.6f}")
    print(f"Latest CO: {co['latest']:.6f}")
    print(f"Status: {alerts['co_status']}")

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