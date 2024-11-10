import React, { useState, useEffect } from 'react';
import { MapContainer, TileLayer, Marker, Popup, GeoJSON } from 'react-leaflet';
import { DefaultIcon, BusStopIcon } from '../utils/LeafletIcons';
import { transportAPI } from '@/config/api';
import type { Stop, Route, ApiResponse } from '@/config/api'; // Importar los tipos desde api.ts
import 'leaflet/dist/leaflet.css';

const TransportMap = () => {
  const [stops, setStops] = useState<Stop[]>([]);
  const [routes, setRoutes] = useState<Route[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const center: [number, number] = [20.9674, -89.6235];

  useEffect(() => {
    const fetchData = async () => {
      try {
        setLoading(true);
        
        // Fetch stops
        const stopsResponse: ApiResponse<{ sample_stops: Stop[] }> = await transportAPI.getStops();
        if (stopsResponse.status === 'success' && stopsResponse.data.sample_stops) {
          setStops(stopsResponse.data.sample_stops);
        }

        // Fetch routes
        const routesResponse: ApiResponse<{ routes: Route[] }> = await transportAPI.getRoutes();
        if (routesResponse.status === 'success' && routesResponse.data.routes) {
          setRoutes(routesResponse.data.routes);
        }

      } catch (error) {
        setError(error instanceof Error ? error.message : 'Error de conexión con el servidor');
        console.error('Error loading data:', error);
      } finally {
        setLoading(false);
      }
    };

    fetchData();
  }, []);

  const routeStyle = {
    color: '#3388ff',
    weight: 3,
    opacity: 0.7
  };

  if (loading) {
    return (
      <div className="bg-white rounded-lg shadow-lg p-4">
        <div className="flex items-center justify-center h-[600px]">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-500"></div>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="bg-white rounded-lg shadow-lg p-4">
        <div className="flex items-center justify-center h-[600px]">
          <div className="text-red-500 text-center">
            <p className="mb-4">{error}</p>
            <button 
              onClick={() => window.location.reload()}
              className="px-4 py-2 bg-blue-500 text-white rounded hover:bg-blue-600 transition-colors"
            >
              Reintentar
            </button>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="bg-white rounded-lg shadow-lg p-4">
      <div className="mb-4">
        <h2 className="text-2xl font-bold text-gray-800">Mapa de Rutas</h2>
        <p className="text-gray-600">
          Visualización de rutas y paradas en tiempo real
          {stops.length > 0 && ` (${stops.length} paradas cargadas)`}
        </p>
      </div>

      <div className="h-[600px] relative rounded-lg overflow-hidden border border-gray-200">
        <MapContainer
          center={center}
          zoom={13}
          className="w-full h-full"
          scrollWheelZoom={true}
        >
          <TileLayer
            attribution='&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors'
            url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
          />

          {stops.map((stop) => (
            <Marker
              key={stop.stop_id}
              position={[stop.stop_lat, stop.stop_lon]}
              icon={BusStopIcon}
            >
              <Popup>
                <div className="p-2">
                  <h3 className="font-bold">{stop.stop_name}</h3>
                  <p className="text-sm text-gray-600">ID: {stop.stop_id}</p>
                  <p className="text-xs text-gray-500">
                    {stop.stop_lat}, {stop.stop_lon}
                  </p>
                </div>
              </Popup>
            </Marker>
          ))}

          {routes.map((route) => (
            <Popup key={route.route_id}>
              <div className="p-2">
                <h3 className="font-bold">{route.route_long_name}</h3>
                <p className="text-sm text-gray-600">ID: {route.route_id}</p>
              </div>
            </Popup>
          ))}
        </MapContainer>
      </div>
    </div>
  );
};

export default TransportMap;