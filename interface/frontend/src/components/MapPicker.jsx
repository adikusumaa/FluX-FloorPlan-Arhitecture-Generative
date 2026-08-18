import { MapContainer, TileLayer, Marker, useMapEvents } from 'react-leaflet';
import { useState } from 'react';
import 'leaflet/dist/leaflet.css';
import L from 'leaflet';

delete L.Icon.Default.prototype._getIconUrl;
L.Icon.Default.mergeOptions({
  iconRetinaUrl: 'https://cdnjs.cloudflare.com/ajax/libs/leaflet/1.7.1/images/marker-icon-2x.png',
  iconUrl: 'https://cdnjs.cloudflare.com/ajax/libs/leaflet/1.7.1/images/marker-icon.png',
  shadowUrl: 'https://cdnjs.cloudflare.com/ajax/libs/leaflet/1.7.1/images/marker-shadow.png',
});

function LocationMarker({ setCoords }) {
  const [position, setPosition] = useState(null);

  useMapEvents({
    click(e) {
      const { lat, lng } = e.latlng;
      setPosition(e.latlng);
      setCoords({ lat, lng });
    },
  });

  return position === null ? null : <Marker position={position} />;
}

export default function MapPicker({ coordinates, onCoordinatesChange }) {
  const defaultCoords = { lat: -6.2088, lng: 106.8456 };
  const center = coordinates || defaultCoords;

  return (
    <div className="h-64 w-full rounded-xl overflow-hidden border border-gray-200">
      <MapContainer
        center={[center.lat, center.lng]}
        zoom={13}
        className="h-full w-full"
      >
        <TileLayer url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png" />
        <LocationMarker setCoords={onCoordinatesChange} />
      </MapContainer>
    </div>
  );
}