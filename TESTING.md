# Automated Testing Guide

## 1. Overview

The project uses Python's built-in `unittest` framework to run automated tests.

The test suite covers:

- Sensor analytics
- Control API
- Control logic
- MQTT messaging
- Kafka integration
- Database connection handling

## 2. Requirements

- Python 3.11 or later
- Project dependencies listed in `Prototype/requirements.txt`

## 3. Install dependencies

From the project root, run:

```powershell
python -m pip install -r Prototype/requirements.txt
```

This installs the dependencies needed by the project and its automated tests, including `httpx2` for the FastAPI test client.

## 4. Run all automated tests

From the project root, execute:

```powershell
python -m unittest discover -s Prototype -p "test_*.py" -v
```

The command automatically discovers and runs all test files matching `test_*.py` inside the `Prototype` directory.

## 5. Current test files

| Test file | Area |
|---|---|
| `test_sensor_analytics.py` | Sensor analytics |
| `test_control_api.py` | Control API |
| `test_control_logic.py` | Control logic |
| `test_messaging_database_integration.py` | Messaging and database integration |

## 6. External services

The automated tests use mocks where external services are involved. MQTT, Kafka and PostgreSQL do not need to be running to execute the automated test suite.

This allows team members to run the tests locally without setting up the complete project infrastructure.

## 7. Expected result

A successful test run displays a summary similar to:

```text
Ran 42 tests

OK
```

If a test fails, check the error message in the terminal and review the relevant test file.

## 8. Notes

- Run commands from the project root unless stated otherwise.
- The `unittest` framework is included with Python, so it does not need to be installed separately.
- Run the full test suite after making changes to the project to check that existing functionality still works.