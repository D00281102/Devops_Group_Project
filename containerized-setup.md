# Containerized Kafka Setup

This guide runs Kafka, Kafka UI, Kafka Connect, Mosquitto, and the Python sensor with Docker Compose.

For the manual Windows setup, see `local-setup.md`.

---

## Architecture

```text
Sensor Container
      |
      | MQTT: mosquitto:1883
      v
Mosquitto Container
      |
      | MQTT Source Connector
      v
Kafka Connect Container
      |
      | Kafka: kafka:9093
      v
Kafka Container
      |
      +--> Kafka UI: http://localhost:8080
      |
      +--> sensor-telemetry topic