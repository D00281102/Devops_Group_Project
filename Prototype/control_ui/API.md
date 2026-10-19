# Control Settings API

## Base URL

`http://127.0.0.1:8000`

## GET /control-settings

Retrieves the current saved control settings from PostgreSQL.

**Successful response: `200 OK`**

```json
{
  "temperature_threshold": 30,
  "humidity_threshold": 75,
  "light_enabled": true
}
```

The values above are an example. The endpoint returns the currently saved values.

## PUT /control-settings

Updates and persists the control settings in the `control_settings` table.

**Request body (JSON)**

```json
{
  "temperature_threshold": 30,
  "humidity_threshold": 75,
  "light_enabled": true
}
```

**Successful response: `200 OK`**

Returns the saved settings in the same JSON format.

## Fields

| Field | Type | Description |
|---|---|---|
| `temperature_threshold` | Number | Temperature threshold in degrees Celsius; accepted range -50 to 100 |
| `humidity_threshold` | Number | Humidity threshold in %; accepted range 0 to 100 |
| `light_enabled` | Boolean | `true` enables the light setting; `false` disables it |

## Validation and persistence

- Invalid threshold values are rejected with `422 Unprocessable Entity`.
- Settings are stored in PostgreSQL, so they persist across page refreshes and API requests.
- The initial defaults are temperature `25`, humidity `70`, and light enabled `true`.

## Local testing

Start the API from the repository root:

```powershell
python -m uvicorn api.main:app --app-dir Prototype --reload
```

Interactive API documentation:

`http://127.0.0.1:8000/docs`
