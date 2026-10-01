from sensor_analytics import analyse_sensor_data

dummy_data = [
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
    },
    {
        "ts": "1594515694",
        "device": "dummy-sensor-1",
        "co": "0.0050",
        "humidity": "62.0",
        "light": "true",
        "lpg": "0.0075",
        "motion": "false",
        "smoke": "0.0210",
        "temp": "23.0"
    },
    {
        "ts": "1594519294",
        "device": "dummy-sensor-2",
        "co": "0.0035",
        "humidity": "70.0",
        "light": "false",
        "lpg": "0.0060",
        "motion": "true",
        "smoke": "0.0180",
        "temp": "20.5"
    }
]

print("Dummy Sensor Analytics Test")
print("===========================")

analyse_sensor_data(dummy_data)