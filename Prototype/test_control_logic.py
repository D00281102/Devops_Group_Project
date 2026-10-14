from Control_Logic import evaluate_sensor_data
from api.db import pool

# Test 1: Default control settings
sensor_data = {
    "temp": 26,
    "humidity": 75,
    "light": True
}

commands = evaluate_sensor_data(sensor_data)

assert len(commands) == 3
assert commands[0]["actuator"] == "fan"
assert commands[1]["actuator"] == "dehumidifier"
assert commands[2]["actuator"] == "light"

print("TEST 1 PASSED: Default settings generated all three commands.")

# Test 2: Custom control settings
custom_settings = {
    "temperature_threshold": 28,
    "humidity_threshold": 80,
    "light_enabled": False
}

commands = evaluate_sensor_data(sensor_data, custom_settings)

assert len(commands) == 0

print("TEST 2 PASSED: Custom settings prevented actuator commands.")

# Test 3: Sensor readings exactly at configured thresholds
boundary_sensor_data = {
    "temp": 25,
    "humidity": 70,
    "light": False
}

commands = evaluate_sensor_data(boundary_sensor_data)

assert len(commands) == 2
assert commands[0]["actuator"] == "fan"
assert commands[1]["actuator"] == "dehumidifier"

print("TEST 3 PASSED: Actuators triggered at exact thresholds.")

# Test 4: Temperature control only
temperature_data = {
    "temp": 30,
    "humidity": 50,
    "light": False
}

commands = evaluate_sensor_data(temperature_data)

assert len(commands) == 1
assert commands[0]["actuator"] == "fan"
assert commands[0]["action"] == "ON"

print("TEST 4 PASSED: Only the fan activated for high temperature.")

# Test 5: Humidity control only
humidity_data = {
    "temp": 20,
    "humidity": 85,
    "light": False
}

commands = evaluate_sensor_data(humidity_data)

assert len(commands) == 1
assert commands[0]["actuator"] == "dehumidifier"
assert commands[0]["action"] == "ON"

print("TEST 5 PASSED: Only the dehumidifier activated for high humidity.")

# Test 6: Light control only
light_data = {
    "temp": 20,
    "humidity": 50,
    "light": True
}

commands = evaluate_sensor_data(light_data)

assert len(commands) == 1
assert commands[0]["actuator"] == "light"
assert commands[0]["action"] == "ON"

print("TEST 6 PASSED: Only the light activated when detected.")

pool.close()
