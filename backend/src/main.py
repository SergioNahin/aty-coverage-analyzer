from fastapi import FastAPI, HTTPException, WebSocket, WebSocketDisconnect, Request
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from typing import List, Dict
import logging
from datetime import datetime
from services.transport_service import TransportDataManager
from models.esquemas import (
    RouteBase,
    AlternativeRoute,
    AGEBAnalysis,
    ServiceResponse
)

# Configuración de logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# FastAPI app
app = FastAPI(title="API de Transporte Mérida")

@app.middleware("http")
async def error_handling_middleware(request: Request, call_next):
    try:
        response = await call_next(request)
        return response
    except Exception as e:
        return JSONResponse(
            content={
                "status": "error",
                "message": str(e)
            },
            status_code=500
        )

# Configura CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE"],
    allow_headers=["*"],
    expose_headers=["*"]
)

# Instancia global del manejador de datos
transport_manager = TransportDataManager()

# WebSocket Manager
class NotificationManager:
    def __init__(self):
        self.active_connections: List[WebSocket] = []
        self.route_status: Dict[str, str] = {}

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.append(websocket)

    def disconnect(self, websocket: WebSocket):
        self.active_connections.remove(websocket)

    async def broadcast_route_update(self, route_id: str, status: str):
        self.route_status[route_id] = status
        message = {
            "type": "route_update",
            "route_id": route_id,
            "status": status,
            "timestamp": datetime.now().isoformat()
        }
        for connection in self.active_connections:
            try:
                await connection.send_json(message)
            except:
                await self.disconnect(connection)

notification_manager = NotificationManager()

@app.get("/")
async def root():
    return JSONResponse(
        content={"message": "API de Transporte Mérida - Sistema Va y Ven"},
        status_code=200
    )

@app.get("/api/rutas")
async def get_routes():
    """Obtener todas las rutas del sistema Va y Ven en formato GeoJSON"""
    try:
        # Convertir el GeoDataFrame a GeoJSON
        routes_geojson = transport_manager.rutas_gdf.to_json()
        return JSONResponse(
            content={
                "status": "success",
                "data": routes_geojson
            },
            status_code=200
        )
    except Exception as e:
        logger.error(f"Error getting routes: {str(e)}")
        return JSONResponse(
            content={
                "status": "error",
                "message": str(e)
            },
            status_code=500
        )

@app.get("/api/paradas")
async def get_stops():
    """Obtener todas las paradas en formato GeoJSON"""
    try:
        # Convertir el GeoDataFrame a GeoJSON
        stops_geojson = transport_manager.paradas_gdf.to_json()
        return JSONResponse(
            content={
                "status": "success",
                "data": stops_geojson
            },
            status_code=200
        )
    except Exception as e:
        logger.error(f"Error getting stops: {str(e)}")
        return JSONResponse(
            content={
                "status": "error",
                "message": str(e)
            },
            status_code=500
        )

@app.get("/api/rutas/{route_id}")
async def get_route(route_id: str):
    """Obtener una ruta específica en formato GeoJSON"""
    try:
        # Filtrar la ruta específica y convertir a GeoJSON
        route = transport_manager.rutas_gdf[transport_manager.rutas_gdf['route_id'] == route_id]
        if len(route) == 0:
            return JSONResponse(
                content={
                    "status": "error",
                    "message": f"Route {route_id} not found"
                },
                status_code=404
            )
        route_geojson = route.to_json()
        return JSONResponse(
            content={
                "status": "success",
                "data": route_geojson
            },
            status_code=200
        )
    except Exception as e:
        logger.error(f"Error getting route {route_id}: {str(e)}")
        return JSONResponse(
            content={
                "status": "error",
                "message": str(e)
            },
            status_code=500
        )

@app.get("/api/rutas/alternativas")
async def get_alternative_routes(origen: str, destino: str):
    """Obtener rutas alternativas entre dos puntos en formato GeoJSON"""
    try:
        if not origen or not destino:
            return JSONResponse(
                content={
                    "status": "error",
                    "message": "Both origen and destino parameters are required"
                },
                status_code=400
            )
            
        alternatives = transport_manager.get_route_alternatives(origen, destino)
        # Asumiendo que alternatives ya está en formato GeoJSON o necesita conversión
        return JSONResponse(
            content={
                "status": "success",
                "data": alternatives
            },
            status_code=200
        )
    except ValueError as e:
        return JSONResponse(
            content={
                "status": "error",
                "message": str(e)
            },
            status_code=404
        )
    except Exception as e:
        logger.error(f"Error in alternative routes: {str(e)}")
        return JSONResponse(
            content={
                "status": "error",
                "message": str(e)
            },
            status_code=500
        )

@app.get("/api/cobertura/{ageb}")
async def get_coverage_analysis(ageb: str):
    """Analizar cobertura en un AGEB específico y devolver en formato GeoJSON"""
    try:
        if not ageb:
            return JSONResponse(
                content={
                    "status": "error",
                    "message": "AGEB parameter is required"
                },
                status_code=400
            )
            
        analysis = transport_manager.analyze_coverage(ageb)
        return JSONResponse(
            content={
                "status": "success",
                "data": analysis
            },
            status_code=200
        )
    except ValueError as e:
        return JSONResponse(
            content={
                "status": "error",
                "message": str(e)
            },
            status_code=404
        )
    except Exception as e:
        logger.error(f"Error in coverage analysis: {str(e)}")
        return JSONResponse(
            content={
                "status": "error",
                "message": str(e)
            },
            status_code=500
        )

@app.websocket("/ws/va-y-ven")
async def websocket_endpoint(websocket: WebSocket):
    await notification_manager.connect(websocket)
    try:
        while True:
            data = await websocket.receive_json()
            if "route_id" in data and "status" in data:
                await notification_manager.broadcast_route_update(
                    data["route_id"],
                    data["status"]
                )
    except WebSocketDisconnect:
        notification_manager.disconnect(websocket)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)