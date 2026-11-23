
from sensor_analytics import analyse_sensor_data

# Test 1: Normal sensor readings
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

print("TEST 1: NORMAL SENSOR READINGS")
normal_results = analyse_sensor_data(normal_data)

assert normal_results["alerts"]["temperature_status"] == "normal"
assert normal_results["alerts"]["humidity_status"] == "normal"
assert normal_results["alerts"]["co_status"] == "normal"

print("TEST 1 PASSED")


# Test 2: High sensor readings
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

print("\nTEST 2: HIGH SENSOR READINGS")
high_results = analyse_sensor_data(high_data)

assert high_results["alerts"]["temperature_status"] == "high"
assert high_results["alerts"]["humidity_status"] == "high"
assert high_results["alerts"]["co_status"] == "high"

print("TEST 2 PASSED")


# Test 3: Low sensor readings
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

print("\nTEST 3: LOW SENSOR READINGS")
low_results = analyse_sensor_data(low_data)

assert low_results["alerts"]["temperature_status"] == "low"
assert low_results["alerts"]["humidity_status"] == "low"
assert low_results["alerts"]["co_status"] == "normal"

print("TEST 3 PASSED")


# Test 4: Empty sensor data
print("\nTEST 4: EMPTY SENSOR DATA")
empty_results = analyse_sensor_data([])

assert empty_results["temperature"] == {}
assert empty_results["humidity"] == {}
assert empty_results["co"] == {}
assert empty_results["alerts"] == {}
assert empty_results["devices"] == {}
assert empty_results["daily_trends"] == {}

print("TEST 4 PASSED")


# Test 5: Readings exactly at the alert thresholds
print("\nTEST 5: THRESHOLD BOUNDARIES")

boundary_data = [
    {
        "ts": "1594512094",
        "device": "boundary-sensor",
        "co": "0.01",
        "humidity": "70.0",
        "light": "false",
        "lpg": "0.0070",
        "motion": "false",
        "smoke": "0.0200",
        "temp": "25.0"
    }
]

boundary_results = analyse_sensor_data(boundary_data)

assert boundary_results["alerts"]["temperature_status"] == "normal"
assert boundary_results["alerts"]["humidity_status"] == "normal"
assert boundary_results["alerts"]["co_status"] == "normal"

print("TEST 5 PASSED")


# Test 6: Multiple readings and analytics calculations
print("\nTEST 6: MULTIPLE SENSOR READINGS")

multiple_data = [
    {
        "ts": "1609502400",
        "device": "sensor-A",
        "co": "0.004",
        "humidity": "40",
        "light": "false",
        "lpg": "0.007",
        "motion": "false",
        "smoke": "0.020",
        "temp": "20"
    },
    {
        "ts": "1609502400",
        "device": "sensor-A",
        "co": "0.016",
        "humidity": "80",
        "light": "true",
        "lpg": "0.008",
        "motion": "false",
        "smoke": "0.021",
        "temp": "30"
    },
    {
        "ts": "1609588800",
        "device": "sensor-B",
        "co": "0.008",
        "humidity": "20",
        "light": "false",
        "lpg": "0.006",
        "motion": "true",
        "smoke": "0.018",
        "temp": "10"
    }
]

multiple_results = analyse_sensor_data(multiple_data)

assert multiple_results["temperature"]["count"] == 3
assert multiple_results["temperature"]["average"] == 20
assert multiple_results["temperature"]["minimum"] == 10
assert multiple_results["temperature"]["maximum"] == 30
assert multiple_results["temperature"]["latest"] == 10

assert multiple_results["humidity"]["count"] == 3
assert round(multiple_results["humidity"]["average"], 2) == 46.67

assert multiple_results["co"]["count"] == 3
assert round(multiple_results["co"]["average"], 6) == 0.009333

print("TEST 6 PASSED")


# Test 7: Per-device analytics
print("\nTEST 7: DEVICE ANALYTICS")

assert multiple_results["devices"]["sensor-A"]["readings"] == 2
assert multiple_results["devices"]["sensor-A"]["average_temperature"] == 25
assert multiple_results["devices"]["sensor-B"]["readings"] == 1
assert multiple_results["devices"]["sensor-B"]["average_temperature"] == 10

print("TEST 7 PASSED")


# Test 8: Daily sensor trends
print("\nTEST 8: DAILY SENSOR TRENDS")

assert len(multiple_results["daily_trends"]) == 2

daily_values = list(multiple_results["daily_trends"].values())

assert daily_values[0]["readings"] == 2
assert daily_values[0]["average_temperature"] == 25
assert daily_values[1]["readings"] == 1
assert daily_values[1]["average_temperature"] == 10

print("TEST 8 PASSED")

print("\nALL SENSOR PROCESSING TESTS PASSED!")
