import csv

DATA_FILE = "Prototype/data/iot_telemetry_data.csv"

temperatures = []

with open(DATA_FILE, "r", newline="") as file:
    reader = csv.DictReader(file)

    for row in reader:
        temperatures.append(float(row["temp"]))

average_temp = sum(temperatures) / len(temperatures)
minimum_temp = min(temperatures)
maximum_temp = max(temperatures)

print("Temperature Analytics")
print("---------------------")
print(f"Number of readings: {len(temperatures)}")
print(f"Average temperature: {average_temp:.2f} °C")
print(f"Minimum temperature: {minimum_temp:.2f} °C")
print(f"Maximum temperature: {maximum_temp:.2f} °C")