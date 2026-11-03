# SCRUM-122 - Multi-Building Control Isolation Test Results

## Objective

Verify that House 1 and House 2 maintain separate control settings, process sensor readings independently, and publish actuator commands to the correct building-specific MQTT topics.

## Test Environment

- Project: DevOps Group Project - IoT Sensor Pipeline
- Test date: 2 November 2026
- Branch: liam/multi-building-control
- Language: Python
- Testing approach: In-process tests using mocked PostgreSQL connections, MQTT clients and building mappings
- Main file tested: Prototype/Control_Logic.py

## Test Scenarios

Both houses received the same simulated sensor readings but used different control settings.

| Setting | House 1 | House 2 |
|---|---|---|
| Building ID | 1 | 2 |
| Temperature threshold | 25 C | 30 C |
| Humidity threshold | 70% | 80% |
| Light enabled | True | False |
| Sensor temperature | 28 C | 28 C |
| Sensor humidity | 75% | 75% |
| Sensor light | True | True |

## Test 1 - Control Decision Isolation

Expected:
- House 1 activates the fan, dehumidifier and light.
- House 2 activates no actuators.

Actual:
- House 1 generated all three expected commands.
- House 2 generated no commands.
- Control decisions remained separate.

Result: PASS

## Test 2 - MQTT Command Isolation

Expected:
- House 1 commands target buildings/1/actuators/commands.
- House 2 commands target buildings/2/actuators/commands.
- Each command contains its correct building ID.

Actual:
- Both building-specific topics were verified using a mocked MQTT client.
- Each JSON payload contained the correct building ID.

Result: PASS

## Test 3 - Sensor-to-Actuator Flow

Expected:
- House 1 sensor readings use House 1 settings and generate three commands.
- House 2 sensor readings use House 2 settings and generate no commands.
- Commands are not sent to another building.

Actual:
- House 1 generated three commands on its own MQTT topic.
- House 2 generated no commands.
- Building mappings and settings were mocked for the test.

Result: PASS

## Test 4 - Database Settings Retrieval

Expected:
- House 1 queries control_settings using building_id = 1.
- House 2 queries control_settings using building_id = 2.
- Each house receives its own configured thresholds.

Actual:
- Both queries used the correct building ID.
- Returned settings matched the simulated values for each house.

Result: PASS

## Summary

| Test | Result |
|---|---|
| Control decision isolation | PASS |
| MQTT command isolation | PASS |
| Sensor-to-actuator flow | PASS |
| Database settings retrieval | PASS |

All four test scenarios passed.

## Limitations and Outstanding Work

- PostgreSQL connections and returned settings were mocked.
- MQTT publishing was tested with a mocked client, not a live broker.
- Building-device mappings were mocked in the sensor-to-actuator test.
- Live database persistence and cross-building update isolation have not been verified.
- Full end-to-end testing with the deployed frontend, authentication database, PostgreSQL and MQTT broker remains outstanding.
- The legacy control settings endpoints were disabled in SCRUM-121 and require frontend migration.
- The admin-only update policy should be confirmed with the team.

## Evidence

Screenshots captured during testing:

1. SCRUM-122-Control-Isolation.png
2. SCRUM-122-MQTT-Isolation.png
3. SCRUM-122-End-to-End-Isolation.png
4. SCRUM-122-Database-Isolation.png

## Conclusion

The tested Control Logic functions correctly separated control decisions, settings queries and MQTT command routing between two simulated buildings.

The mocked isolation tests passed. Live integration testing is still required before confirming production-level multi-building isolation.
