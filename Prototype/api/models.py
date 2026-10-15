from pydantic import BaseModel, Field
from typing import Optional

class TelemetryRow(BaseModel):
    """
    One row of iot_telemetry_data, as returned by the API.
    Includes the auto-generated records column.
    """
    records: Optional[int] = None
    ts: float
    device: str
    co: float
    humidity: float
    light: bool
    lpg: float
    motion: bool
    smoke: float
    temp: float

class TelemetryCreate(BaseModel):
    """
    One row of iot_telemetry_data, as sent to the API.
    Does not include the auto-generated records column.
    """
    ts: float
    device: str
    co: float
    humidity: float
    light: bool
    lpg: float
    motion: bool
    smoke: float
    temp: float

class TelemetryUpdate(BaseModel):
    """
    One row of iot_telemetry_data, as sent to the API.
    Does not include the auto-generated records column.
    Only send what you want to update. All fields are optional.
    """
    ts: Optional[float] = None
    device: Optional[str] = None
    co: Optional[float] = None
    humidity: Optional[float] = None
    light: Optional[bool] = None
    lpg: Optional[float] = None
    motion: Optional[bool] = None
    smoke: Optional[float] = None
    temp: Optional[float] = None


class ControlSettings(BaseModel):
    """
    Control settings saved in the control_settings database.
    """
    temperature_threshold: float = Field(
        default=25.0,
        ge=-50,
        le=100
    )
    humidity_threshold: float = Field(
        default=70.0,
        ge=0,
        le=100
    )
    light_enabled: bool = True
