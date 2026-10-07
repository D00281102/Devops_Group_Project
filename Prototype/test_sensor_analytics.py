from sensor_analytics import analyse_sensor_data

normal_data = [
    {
        "ts": "1594512094",
        "device": "dummy-sensor-1",
        "co": "0.0045",
        "humidity": "60.0",
        "light": "false",
        "lpg": "0.0070",
        "motion": "false",
        "smoke": "0.0200",
        "temp": "22.5"
    }
]

high_data = [
    {
        "ts": "1594515694",
        "device": "dummy-sensor-2",
        "co": "0.0150",
        "humidity": "85.0",
        "light": "true",
        "lpg": "0.0075",
        "motion": "false",
        "smoke": "0.0210",
        "temp": "29.0"
    }
]

low_data = [
    {
        "ts": "1594519294",
        "device": "dummy-sensor-3",
        "co": "0.0035",
        "humidity": "20.0",
        "light": "false",
        "lpg": "0.0060",
        "motion": "true",
        "smoke": "0.0180",
        "temp": "5.0"
    }
]

print("NORMAL STATUS TEST")
print("==================")
normal_results = analyse_sensor_data(normal_data)

assert normal_results["alerts"]["temperature_status"] == "normal"
assert normal_results["alerts"]["humidity_status"] == "normal"
assert normal_results["alerts"]["co_status"] == "normal"

print()
print("HIGH STATUS TEST")
print("================")
high_results = analyse_sensor_data(high_data)

assert high_results["alerts"]["temperature_status"] == "high"
assert high_results["alerts"]["humidity_status"] == "high"
assert high_results["alerts"]["co_status"] == "high"

print()
print("LOW STATUS TEST")
print("===============")
low_results = analyse_sensor_data(low_data)

assert low_results["alerts"]["temperature_status"] == "low"
assert low_results["alerts"]["humidity_status"] == "low"
assert low_results["alerts"]["co_status"] == "normal"

print()
print("All sensor alert tests passed.")