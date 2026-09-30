\# Sensor Data Analytics



\## Overview



This part of the project analyses environmental sensor data so that useful values, patterns and trends can be identified from the raw sensor readings.



The analytics code is implemented in:



`Prototype/sensor\_analytics.py`



The current implementation uses the Environmental Sensor Telemetry Data dataset and processes temperature, humidity and CO readings.



The analytics can later be connected to sensor data retrieved from the shared PostgreSQL/TimescaleDB database.



\---



\## Dataset



Dataset:



\*\*Environmental Sensor Telemetry Data\*\*



Source: Kaggle  

Author: Gary A. Stafford



The CSV file used for local testing is:



`iot\_telemetry\_data.csv`



The dataset contains \*\*405,184 sensor readings\*\*.



The available fields are:



\- `ts` - Unix timestamp

\- `device` - sensor device identifier

\- `co` - carbon monoxide reading

\- `humidity` - humidity reading

\- `light` - light status

\- `lpg` - LPG reading

\- `motion` - motion status

\- `smoke` - smoke reading

\- `temp` - temperature reading



The dataset is stored locally in:



`Prototype/data/iot\_telemetry\_data.csv`



The `Prototype/data/` directory is excluded from Git because the dataset is large.



\---



\## Current Analytics



The current implementation performs several types of analysis.



\### Temperature Analytics



The program calculates:



\- Number of temperature readings

\- Average temperature

\- Minimum temperature

\- Maximum temperature



Tested results:



\- Readings: 405,184

\- Average: 22.45 °C

\- Minimum: 0.00 °C

\- Maximum: 30.60 °C



\### Humidity Analytics



The program calculates:



\- Number of humidity readings

\- Average humidity

\- Minimum humidity

\- Maximum humidity



Tested results:



\- Readings: 405,184

\- Average: 60.51%

\- Minimum: 1.10%

\- Maximum: 99.90%



\### CO Analytics



The program calculates:



\- Number of CO readings

\- Average CO

\- Minimum CO

\- Maximum CO



Tested results:



\- Readings: 405,184

\- Average: 0.004639

\- Minimum: 0.001171

\- Maximum: 0.014420



\---



\## Per-Device Analytics



The analytics program groups readings by sensor device.



For each device it calculates:



\- Number of readings

\- Average temperature

\- Average humidity



This allows readings from different sensor devices to be compared and helps identify differences between sensors.



Current results:



\### Device `b8:27:eb:bf:9d:51`



\- Readings: 187,451

\- Average temperature: 22.28 °C

\- Average humidity: 50.81%



\### Device `00:0f:00:70:91:0a`



\- Readings: 111,815

\- Average temperature: 19.36 °C

\- Average humidity: 75.44%



\### Device `1c:bf:ce:15:ec:4d`



\- Readings: 105,918

\- Average temperature: 26.03 °C

\- Average humidity: 61.91%



\---



\## Daily Trend Analytics



The Unix timestamp stored in the `ts` field is converted into a date.



Sensor readings are then grouped by day.



For each day the program calculates:



\- Number of readings

\- Average temperature

\- Average humidity



The current dataset covers approximately:



\*\*12 July 2020 - 20 July 2020\*\*



This allows changes in temperature and humidity to be observed over time instead of analysing the complete dataset as one group.



The final day contains fewer readings because the dataset only contains part of that day.



\---



\## Running the Analytics



From the project root directory run:



```bash

python Prototype/sensor\_analytics.py

