import geopandas as gpd
from shapely.geometry import Point
import logging
from typing import List, Dict, Optional
from pathlib import Path
from src.models.esquemas import (
    AGEBAnalysis, 
    AlternativeRoute,
    GTFSRoute,
    GTFSStop,
    RouteStatus
)
from src.utils.geojson_handler import GeoJSONHandler

logger = logging.getLogger(__name__)

class TransportDataManager:
    def __init__(self):
        self.geo_handler = GeoJSONHandler()
        self.rutas_gdf = None
        self.paradas_gdf = None
        self.aforo_gdf = None
        self.gtfs_data = None
        self._load_data()

    def _load_data(self):
        """Cargar los archivos GeoJSON y GTFS"""
        try:
            # Cargar datos GTFS y GeoJSON
            self.gtfs_data = self.geo_handler.load_gtfs_data()
            geojson_data = self.geo_handler.load_geojson_data()
            
            # Log datos cargados
            logger.info("Archivos cargados:")
            for key in geojson_data:
                logger.info(f"- {key}")
            
            # Asignar datos GeoJSON
            self.paradas_gdf = geojson_data.get('paradas')
            self.aforo_gdf = geojson_data.get('aforo')
            
            # Verificar datos de paradas
            if self.paradas_gdf is not None and not self.paradas_gdf.empty:
                stop_ids = self.paradas_gdf['stop_id'].tolist()
                logger.info(f"Paradas disponibles: {stop_ids[:5]}... (total: {len(stop_ids)})")
            else:
                logger.error("No se encontraron datos de paradas")
            
            # Verificar datos de aforo
            if self.aforo_gdf is not None and not self.aforo_gdf.empty:
                agebs = self.aforo_gdf['CVE_AGEB'].unique().tolist()
                logger.info(f"AGEBs disponibles: {agebs[:5]}... (total: {len(agebs)})")
            else:
                logger.error("No se encontraron datos de aforo")
            
            # Combinar datos de rutas
            self.rutas_gdf = self.geo_handler.combine_route_data(
                self.gtfs_data, 
                geojson_data
            )
            
            if self.rutas_gdf is None or self.rutas_gdf.empty:
                logger.error("No se encontraron datos de rutas")
            
        except Exception as e:
            logger.error(f"Error en carga de datos: {str(e)}")
            raise

    def get_route_alternatives(self, origin_id: str, destination_id: str) -> List[AlternativeRoute]:
        """Encontrar rutas alternativas entre dos puntos"""
        try:
            # Verificar que los datos de paradas existen
            if self.paradas_gdf is None or self.paradas_gdf.empty:
                raise ValueError("No hay datos de paradas disponibles")
            
            logger.info(f"Buscando ruta: {origin_id} -> {destination_id}")
            
            # Verificar origen
            origin_stop = self.paradas_gdf[self.paradas_gdf['stop_id'] == origin_id]
            if origin_stop.empty:
                logger.error(f"Parada de origen no encontrada: {origin_id}")
                raise ValueError(f"Stop not found: {origin_id}")
            
            # Verificar destino
            dest_stop = self.paradas_gdf[self.paradas_gdf['stop_id'] == destination_id]
            if dest_stop.empty:
                logger.error(f"Parada de destino no encontrada: {destination_id}")
                raise ValueError(f"Stop not found: {destination_id}")
            
            # Obtener coordenadas
            origin_point = Point(origin_stop.iloc[0].geometry.x, origin_stop.iloc[0].geometry.y)
            dest_point = Point(dest_stop.iloc[0].geometry.x, dest_stop.iloc[0].geometry.y)
            
            # Buscar alternativas
            alternatives_data = self.geo_handler.find_alternative_routes(
                origin_point,
                dest_point
            )
            
            return [
                AlternativeRoute(
                    origen=origin_id,
                    destino=destination_id,
                    ruta_principal=alt['ruta_principal'],
                    ruta_alterna=alt['ruta_alterna'],
                    tiempo_estimado=alt['tiempo_estimado'],
                    transbordos=alt['puntos_transbordo']
                ) for alt in alternatives_data
            ]
            
        except Exception as e:
            logger.error(f"Error en búsqueda de rutas alternativas: {str(e)}")
            raise

    def analyze_coverage(self, ageb: str) -> AGEBAnalysis:
        """Analizar cobertura en un AGEB específico"""
        try:
            # Verificar que los datos de aforo existen
            if self.aforo_gdf is None or self.aforo_gdf.empty:
                raise ValueError("No hay datos de aforo disponibles")
            
            logger.info(f"Analizando AGEB: {ageb}")
            
            # Verificar si el AGEB existe
            if not any(self.aforo_gdf['CVE_AGEB'] == ageb):
                logger.error(f"AGEB no encontrado: {ageb}")
                raise ValueError(f"AGEB {ageb} not found in data")
            
            # Preparar datos para análisis
            coverage_data = self.geo_handler.analyze_coverage(
                {
                    'aforo': self.aforo_gdf,
                    'paradas': self.paradas_gdf
                },
                ageb
            )
        
            if not coverage_data:
                raise ValueError(f"No se encontraron datos de cobertura para el AGEB {ageb}")
            
            # Crear el objeto AGEBAnalysis con los datos procesados
            analysis = AGEBAnalysis(
                cve_ageb=ageb,
                up_net=int(coverage_data['total_ascensos']),
                down_net=int(coverage_data['total_descensos']),
                flujo=int(coverage_data['flujo_total']),
                aforo=float(coverage_data['aforo_promedio']),  # Aseguramos que es float
                horas_pico=coverage_data.get('horas_pico', [])
            )
            
            return analysis
                
        except Exception as e:
            logger.error(f"Error en análisis de cobertura: {str(e)}")
            raise
