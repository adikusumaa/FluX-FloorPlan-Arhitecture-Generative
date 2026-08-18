import { describe, it, expect, vi } from 'vitest';
import { render, screen } from '@testing-library/react';
import MapPicker from '../MapPicker';

// Mock library Leaflet dengan vi (bukan jest)
vi.mock('react-leaflet', () => ({
  MapContainer: ({ children }) => <div data-testid="map-container">{children}</div>,
  TileLayer: () => <div>TileLayer</div>,
  Marker: () => <div>Marker</div>,
  useMapEvents: () => null,
}));

describe('MapPicker Component', () => {
  it('harus merender container peta', () => {
    const mockSetCoords = vi.fn(); // pakai vi.fn() bukan jest.fn()
    const coords = { lat: -6.2, lng: 106.8 };

    render(<MapPicker coordinates={coords} onCoordinatesChange={mockSetCoords} />);
    
    const mapElement = screen.getByTestId('map-container');
    expect(mapElement).toBeInTheDocument();
  });
});