import React, { useState, useEffect } from 'react';
import { MapContainer, TileLayer, Marker, Popup } from 'react-leaflet';
import { DefaultIcon, BusStopIcon } from '../utils/LeafletIcons';
import 'leaflet/dist/leaflet.css';

const TransportMap = () => {
  const [stops, setStops] = useState([]);
  const center: [number, number] = [20.9674, -89.6235]; // Coordenadas de Mérida

  useEffect(() => {
    const fetchStops = async () => {
      try {
        const response = await fetch('http://localhost:8000/api/debug/paradas');
        const data = await response.json();
        if (data.status === 'success') {
          setStops(data.data.sample_stops);
        }
      } catch (error) {
        console.error('Error loading stops:', error);
      }
    };

    fetchStops();
  }, []);

  return (
    <div className="bg-white rounded-lg shadow-lg p-4">
      <div className="mb-4">
        <h2 className="text-2xl font-bold text-gray-800">Mapa de Rutas</h2>
        <p className="text-gray-600">Visualización de rutas y paradas en tiempo real</p>
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
              Centro de Mérida
            </Popup>
          </Marker>

          {stops.map((stop: any) => (
            <Marker
              key={stop.stop_id}
              position={[stop.stop_lat, stop.stop_lon]}
              icon={BusStopIcon}
            >
              <Popup>
                <div className="p-2">
                  <h3 className="font-bold">{stop.stop_name}</h3>
                  <p className="text-sm">{stop.stop_id}</p>
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