import os
import psycopg2

from sensor_analytics import analyse_sensor_data


DB_HOST = os.getenv("DB_HOST", "192.168.1.8")
DB_PORT = os.getenv("DB_PORT", "5434")
DB_NAME = os.getenv("DB_NAME", "postgres")
DB_USER = os.getenv("DB_USER", "postgres")
DB_PASSWORD = os.getenv("DB_PASSWORD")


def get_sensor_data():
    if not DB_PASSWORD:
        raise RuntimeError(
            "DB_PASSWORD environment variable is not set."
        )

    connection = psycopg2.connect(
        host=DB_HOST,
        port=DB_PORT,
        database=DB_NAME,
        user=DB_USER,
        password=DB_PASSWORD
    )

    try:
        cursor = connection.cursor()

        cursor.execute("""
            SELECT
                ts,
                device,
                co,
                humidity,
                light,
                lpg,
                motion,
                smoke,
                temp
            FROM iot_telemetry_data
            ORDER BY records
        """)

        columns = [description[0] for description in cursor.description]

        rows = [
            dict(zip(columns, row))
            for row in cursor.fetchall()
        ]

        cursor.close()

        return rows

    finally:
        connection.close()


if __name__ == "__main__":
    sensor_data = get_sensor_data()

    print(f"Retrieved {len(sensor_data)} sensor readings from PostgreSQL.")
    print()

    analyse_sensor_data(sensor_data)