import csv

DATA_FILE = "Prototype/data/iot_telemetry_data.csv"

temperatures = []
humidities = []

with open(DATA_FILE, "r", newline="") as file:
    reader = csv.DictReader(file)

    for row in reader:
        temperatures.append(float(row["temp"]))
        humidities.append(float(row["humidity"]))

# Temperature analytics
average_temp = sum(temperatures) / len(temperatures)
minimum_temp = min(temperatures)
maximum_temp = max(temperatures)

# Humidity analytics
average_humidity = sum(humidities) / len(humidities)
minimum_humidity = min(humidities)
maximum_humidity = max(humidities)

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