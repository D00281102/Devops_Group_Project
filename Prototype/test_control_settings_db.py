from getpass import getpass
import psycopg


DB_HOST = "localhost"
DB_PORT = 5432
DB_NAME = "control_settings_db"
DB_USER = "postgres"


def test_control_settings_database():
    password = getpass("PostgreSQL password: ")

    with psycopg.connect(
        host=DB_HOST,
        port=DB_PORT,
        dbname=DB_NAME,
        user=DB_USER,
        password=password
    ) as connection:
        with connection.cursor() as cursor:
            cursor.execute(
                """
                SELECT
                    id,
                    temperature_threshold,
                    humidity_threshold,
                    light_enabled,
                    updated_at
                FROM control_settings
                WHERE id = 1;
                """
            )

            row = cursor.fetchone()

    if row is None:
        print("No control settings found.")
        return

    print()
    print("Control Settings Database Test")
    print("------------------------------")
    print(f"ID: {row[0]}")
    print(f"Temperature threshold: {row[1]}")
    print(f"Humidity threshold: {row[2]}")
    print(f"Light enabled: {row[3]}")
    print(f"Updated at: {row[4]}")
    print()
    print("Database connection and read test passed.")


if __name__ == "__main__":
    test_control_settings_database()