import geopandas as gpd
import pandas as pd
from pathlib import Path
from typing import Dict, Any, Optional, Union, List
import logging
from shapely.geometry import Point, LineString
import os

logger = logging.getLogger(__name__)

logger = logging.getLogger(__name__)

class GeoJSONHandler:
    def __init__(self):
        self.base_path = Path(__file__).parent.parent.parent
        self.data_path = self.base_path / "data"
        self.gtfs_path = self.data_path / "gtfs"

    def load_gtfs_data(self) -> Dict[str, pd.DataFrame]:
        """Cargar todos los archivos GTFS"""
        gtfs_files = {
            'agency': 'agency.txt',
            'calendar': 'calendar.txt',
            'fare_attributes': 'fare_attributes.txt',
            'fare_rules': 'fare_rules.txt',
            'feed_info': 'feed_info.txt',
            'routes': 'routes.txt',
            'shapes': 'shapes.txt',
            'stop_times': 'stop_times.txt',
            'stops': 'stops.txt',
            'trips': 'trips.txt'
        }

        gtfs_data = {}
        try:
            for key, filename in gtfs_files.items():
                file_path = self.gtfs_path / filename
                if file_path.exists():
                    gtfs_data[key] = pd.read_csv(file_path)
                    logger.info(f"Loaded GTFS file: {filename}")
                else:
                    logger.warning(f"GTFS file not found: {filename}")
            
            return gtfs_data
        except Exception as e:
            logger.error(f"Error loading GTFS data: {e}")
            raise

    def load_geojson_data(self) -> Dict[str, gpd.GeoDataFrame]:
        """Cargar todos los archivos GeoJSON"""
        try:
            geojson_files = {
                'aforo': self.data_path / 'aforo.geojson',
                'paradas': self.data_path / 'paradas.geojson'
            }

            geojson_data = {}
            for key, file_path in geojson_files.items():
                if file_path.exists():
                    geojson_data[key] = gpd.read_file(str(file_path))
                    logger.info(f"Loaded GeoJSON file: {file_path.name}")
                else:
                    logger.warning(f"GeoJSON file not found: {file_path.name}")

            return geojson_data
        except Exception as e:
            logger.error(f"Error loading GeoJSON data: {e}")
            raise

    def combine_route_data(self, gtfs_data: Dict[str, pd.DataFrame], 
                         geojson_data: Dict[str, gpd.GeoDataFrame]) -> gpd.GeoDataFrame:
        """Combinar datos de rutas"""
        try:
            # Obtener rutas básicas del GTFS
            routes_df = gtfs_data.get('routes', pd.DataFrame())
            
            if routes_df.empty:
                logger.warning("No routes data found in GTFS")
                return gpd.GeoDataFrame()

            # Crear GeoDataFrame con datos mínimos necesarios
            routes_gdf = gpd.GeoDataFrame(
                {
                    'route_id': routes_df['route_id'],
                    'route_long_name': routes_df['route_long_name'],
                    'geometry': None  # Placeholder para geometría
                }
            )

            # Si existe shapes.txt, intentar añadir geometrías
            if 'shapes' in gtfs_data and not gtfs_data['shapes'].empty:
                try:
                    shapes_df = gtfs_data['shapes']
                    # Crear geometrías de las rutas si es posible
                    shapes_grouped = shapes_df.groupby('shape_id').agg({
                        'shape_pt_lat': list,
                        'shape_pt_lon': list
                    })
                    
                    # Crear LineStrings para cada shape
                    shapes_grouped['geometry'] = shapes_grouped.apply(
                        lambda x: LineString(zip(x.shape_pt_lon, x.shape_pt_lat)), 
                        axis=1
                    )

                    # Intentar unir con routes si hay una conexión en trips
                    if 'trips' in gtfs_data and not gtfs_data['trips'].empty:
                        trips_df = gtfs_data['trips']
                        if 'shape_id' in trips_df.columns:
                            route_shapes = trips_df.groupby('route_id')['shape_id'].first()
                            for route_id, shape_id in route_shapes.items():
                                if shape_id in shapes_grouped.index:
                                    idx = routes_gdf[routes_gdf.route_id == route_id].index
                                    if not idx.empty:
                                        routes_gdf.loc[idx, 'geometry'] = shapes_grouped.loc[shape_id, 'geometry']

                except Exception as e:
                    logger.warning(f"Could not process shapes data: {e}")

            # Si no hay geometrías, crear una línea simple para visualización
            for idx in routes_gdf[routes_gdf.geometry.isna()].index:
                routes_gdf.loc[idx, 'geometry'] = LineString([(0, 0), (0, 0)])

            return routes_gdf

        except Exception as e:
            logger.error(f"Error combining route data: {e}")
            raise

    def analyze_coverage(self, geojson_data: Dict[str, gpd.GeoDataFrame], 
                        ageb: str) -> Dict[str, Any]:
        """Analizar cobertura de transporte en un AGEB"""
        try:
            aforo_data = geojson_data['aforo']
            ageb_data = aforo_data[aforo_data.CVE_AGEB == ageb]

            if ageb_data.empty:
                logger.warning(f"No data found for AGEB: {ageb}")
                return None

            # Calcular métricas
            analysis = {
                'total_ascensos': int(ageb_data.up_net.sum()),
                'total_descensos': int(ageb_data.down_net.sum()),
                'flujo_total': int(ageb_data.flujo.sum()),
                'aforo_promedio': float(ageb_data.aforo.mean()),
                'horas_pico': self._calculate_peak_hours(ageb_data)
            }

            return analysis
        except Exception as e:
            logger.error(f"Error analyzing coverage for AGEB {ageb}: {e}")
            raise

    def _calculate_peak_hours(self, ageb_data: gpd.GeoDataFrame) -> list:
        """Calcular horas pico basado en aforo"""
        try:
            if 'hora' in ageb_data.columns:
                hourly_data = ageb_data.groupby('hora')['aforo'].mean()
                peak_hours = hourly_data.nlargest(3)
                return [
                    {"hora": str(hora), "aforo": float(aforo)}
                    for hora, aforo in peak_hours.items()
                ]
            return []
        except Exception as e:
            logger.warning(f"Could not calculate peak hours: {e}")
            return []

    def find_alternative_routes(self, 
                              origin: Point, 
                              destination: Point,
                              max_distance: float = 0.001) -> List[Dict[str, Any]]:
        """
        Encontrar rutas alternativas entre dos puntos.
        
        Args:
            origin (Point): Punto de origen
            destination (Point): Punto de destino
            max_distance (float): Distancia máxima para buscar rutas cercanas
            
        Returns:
            List[Dict[str, Any]]: Lista de rutas alternativas
        """
        try:
            # Por ahora retornamos datos de ejemplo
            return [{
                "ruta_principal": "R1",
                "ruta_alterna": "R2",
                "tiempo_estimado": 30,
                "puntos_transbordo": ["P1", "P2"]
            }]
        except Exception as e:
            logger.error(f"Error finding alternative routes: {e}")
            return []