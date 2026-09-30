import csv

DATA_FILE = "Prototype/data/iot_telemetry_data.csv"

temperatures = []
humidities = []
co_readings = []

# Store readings separately for each sensor device
device_data = {}

with open(DATA_FILE, "r", newline="") as file:
    reader = csv.DictReader(file)

    for row in reader:
        temperature = float(row["temp"])
        humidity = float(row["humidity"])
        co = float(row["co"])
        device = row["device"]

        temperatures.append(temperature)
        humidities.append(humidity)
        co_readings.append(co)

        if device not in device_data:
            device_data[device] = {
                "temperatures": [],
                "humidities": []
            }

        device_data[device]["temperatures"].append(temperature)
        device_data[device]["humidities"].append(humidity)

# Temperature analytics
average_temp = sum(temperatures) / len(temperatures)
minimum_temp = min(temperatures)
maximum_temp = max(temperatures)

# Humidity analytics
average_humidity = sum(humidities) / len(humidities)
minimum_humidity = min(humidities)
maximum_humidity = max(humidities)

# CO analytics
average_co = sum(co_readings) / len(co_readings)
minimum_co = min(co_readings)
maximum_co = max(co_readings)

print("Temperature Analytics")
print("---------------------")
print(f"Number of readings: {len(temperatures)}")
print(f"Average temperature: {average_temp:.2f} °C")
print(f"Minimum temperature: {minimum_temp:.2f} °C")
print(f"Maximum temperature: {maximum_temp:.2f} °C")

print()

print("Humidity Analytics")
print("------------------")
print(f"Number of readings: {len(humidities)}")
print(f"Average humidity: {average_humidity:.2f} %")
print(f"Minimum humidity: {minimum_humidity:.2f} %")
print(f"Maximum humidity: {maximum_humidity:.2f} %")

print()

print("CO Analytics")
print("------------")
print(f"Number of readings: {len(co_readings)}")
print(f"Average CO: {average_co:.6f}")
print(f"Minimum CO: {minimum_co:.6f}")
print(f"Maximum CO: {maximum_co:.6f}")

print()

print("Per-Device Analytics")
print("--------------------")

for device, readings in device_data.items():
    device_temperatures = readings["temperatures"]
    device_humidities = readings["humidities"]

    average_device_temp = sum(device_temperatures) / len(device_temperatures)
    average_device_humidity = sum(device_humidities) / len(device_humidities)

    print(f"Device: {device}")
    print(f"Readings: {len(device_temperatures)}")
    print(f"Average temperature: {average_device_temp:.2f} °C")
    print(f"Average humidity: {average_device_humidity:.2f} %")
    print()