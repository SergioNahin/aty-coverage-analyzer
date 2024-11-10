import React, { useState, useEffect } from 'react';
import { MapContainer, TileLayer, Marker, Popup } from 'react-leaflet';
import { DefaultIcon, BusStopIcon } from '../utils/LeafletIcons';
import { transportAPI } from '@/config/api'; // Importamos solo transportAPI
import 'leaflet/dist/leaflet.css';

// Definimos la interfaz Stop aquí
interface Stop {
  stop_id: string;
  stop_name: string;
  stop_lat: number;
  stop_lon: number;
}

const TransportMap = () => {
  const [stops, setStops] = useState<Stop[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const center: [number, number] = [20.9674, -89.6235]; // Coordenadas de Mérida

  useEffect(() => {
    const fetchStops = async () => {
      try {
        setLoading(true);
        const response = await transportAPI.getStops();
        
        if (response.status === 'success' && response.data.sample_stops) {
          setStops(response.data.sample_stops);
        } else {
          setError('No se pudieron cargar las paradas');
        }
      } catch (error) {
        setError(error instanceof Error ? error.message : 'Error de conexión con el servidor');
        console.error('Error loading stops:', error);
      } finally {
        setLoading(false);
      }
    };

    fetchStops();
  }, []);

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

          <Marker position={center} icon={DefaultIcon}>
            <Popup>
              <div className="p-2">
                <h3 className="font-bold">Centro de Mérida</h3>
                <p className="text-sm text-gray-600">Punto de referencia central</p>
              </div>
            </Popup>
          </Marker>

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
                    {stop.stop_lat.toFixed(6)}, {stop.stop_lon.toFixed(6)}
                  </p>
                </div>
              </Popup>
            </Marker>
          ))}
        </MapContainer>
      </div>
    </div>
  );
};

export default TransportMap;