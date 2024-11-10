from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime, time

class RouteBase(BaseModel):
    route_id: str
    route_long_name: str
    route_type: Optional[int] = None

class StopBase(BaseModel):
    stop_id: str
    stop_name: str
    stop_lat: Optional[float] = None
    stop_lon: Optional[float] = None

class AGEBAnalysis(BaseModel):
    cve_ageb: str
    up_net: int
    down_net: int
    flujo: int
    aforo: float
    horas_pico: Optional[List[dict]] = None

class TransferPoint(BaseModel):
    stop_id: str
    stop_name: str
    tiempo_espera: int

class AlternativeRoute(BaseModel):
    origen: str
    destino: str
    ruta_principal: str
    ruta_alterna: str
    tiempo_estimado: int
    transbordos: List[str]

class RouteStatus(BaseModel):
    route_id: str
    status: str
    timestamp: datetime
    location: Optional[dict] = None

class GTFSTimeData(BaseModel):
    arrival_time: str
    departure_time: str
    stop_sequence: int

class GTFSRoute(BaseModel):
    route_id: str
    route_short_name: Optional[str]
    route_long_name: str
    route_type: int

class GTFSStop(BaseModel):
    stop_id: str
    stop_name: str
    stop_lat: float
    stop_lon: float
    location_type: Optional[int] = None
    parent_station: Optional[str] = None

class GTFSTrip(BaseModel):
    trip_id: str
    route_id: str
    service_id: str
    trip_headsign: Optional[str] = None
    direction_id: Optional[int] = None

class ServiceResponse(BaseModel):
    status: str = "success"
    data: Optional[dict] = None
    message: Optional[str] = None