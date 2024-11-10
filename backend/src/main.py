from fastapi import FastAPI, HTTPException, WebSocket, WebSocketDisconnect
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

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
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

# Endpoints
@app.get("/")
async def root():
    return {"message": "API de Transporte Mérida - Sistema Va y Ven"}

@app.get("/api/rutas")
async def get_routes():
    """Obtener todas las rutas del sistema Va y Ven"""
    try:
        routes = transport_manager.rutas_gdf[['route_id', 'route_long_name']].to_dict('records')
        return ServiceResponse(
            status="success",
            data={"routes": routes}
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/rutas/alternativas")
async def get_alternative_routes(origen: str, destino: str):
    """Obtener rutas alternativas entre dos puntos"""
    try:
        if not origen or not destino:
            raise HTTPException(
                status_code=400,
                detail="Both origen and destino parameters are required"
            )
            
        alternatives = transport_manager.get_route_alternatives(origen, destino)
        return ServiceResponse(
            status="success",
            data={"alternatives": alternatives}
        )
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        logger.error(f"Error in alternative routes: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/cobertura/{ageb}")
async def get_coverage_analysis(ageb: str):
    """Analizar cobertura en un AGEB específico"""
    try:
        if not ageb:
            raise HTTPException(
                status_code=400,
                detail="AGEB parameter is required"
            )
            
        analysis = transport_manager.analyze_coverage(ageb)
        return ServiceResponse(
            status="success",
            data={"analysis": analysis}
        )
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        logger.error(f"Error in coverage analysis: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))
@app.get("/api/debug/agebs")
async def get_available_agebs():
    """Obtener lista de AGEBs disponibles"""
    try:
        if transport_manager.aforo_gdf is not None:
            agebs = transport_manager.aforo_gdf['CVE_AGEB'].unique().tolist()
            return ServiceResponse(
                status="success",
                data={
                    "total_agebs": len(agebs),
                    "sample_agebs": agebs[:20]  # Mostrar primeros 20 AGEBs
                }
            )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/debug/paradas")
async def get_available_stops():
    """Obtener lista de paradas disponibles"""
    try:
        if transport_manager.paradas_gdf is not None:
            stops = transport_manager.paradas_gdf['stop_id'].unique().tolist()
            return ServiceResponse(
                status="success",
                data={
                    "total_stops": len(stops),
                    "sample_stops": stops[:20]  # Mostrar primeras 20 paradas
                }
            )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/debug/stats")
async def get_system_stats():
    """Obtener estadísticas generales del sistema"""
    try:
        stats = {
            "total_agebs": len(transport_manager.aforo_gdf['CVE_AGEB'].unique()) if transport_manager.aforo_gdf is not None else 0,
            "total_paradas": len(transport_manager.paradas_gdf) if transport_manager.paradas_gdf is not None else 0,
            "total_rutas": len(transport_manager.rutas_gdf) if transport_manager.rutas_gdf is not None else 0,
            "aforo_total": float(transport_manager.aforo_gdf['aforo'].sum()) if transport_manager.aforo_gdf is not None else 0,
            "top_agebs_por_aforo": []
        }
        
        if transport_manager.aforo_gdf is not None:
            # Obtener top 5 AGEBs por aforo
            top_agebs = transport_manager.aforo_gdf.groupby('CVE_AGEB')['aforo'].mean().nlargest(5)
            stats["top_agebs_por_aforo"] = [
                {"ageb": ageb, "aforo_promedio": float(aforo)}
                for ageb, aforo in top_agebs.items()
            ]
            
        return ServiceResponse(
            status="success",
            data=stats
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

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