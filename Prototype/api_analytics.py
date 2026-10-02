import requests

from sensor_analytics import analyse_sensor_data


API_URL = "http://127.0.0.1:8000/telemetry/?limit=100"


def get_sensor_data_from_api():
    response = requests.get(API_URL, timeout=10)
    response.raise_for_status()

    return response.json()


def get_analytics_results():
    sensor_data = get_sensor_data_from_api()

    print(f"Retrieved {len(sensor_data)} sensor readings from API.")
    print()

    return analyse_sensor_data(sensor_data)


if __name__ == "__main__":
    results = get_analytics_results()