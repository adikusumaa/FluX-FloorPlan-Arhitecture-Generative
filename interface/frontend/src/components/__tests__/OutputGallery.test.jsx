import { describe, it, expect, vi } from 'vitest';
import { render, screen, fireEvent } from '@testing-library/react';
import OutputGallery from '../OutputGallery';

// Data dummy Base64
const dummyResults = [
  {
    id: '1',
    rank: 1,
    style: 'Modern',
    image_url: 'data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mP8z8BQDwAEhQGAhKmMIQAAAABJRU5ErkJggg==',
    scores: { composite: 0.85 },
    energy: { EUI: 120, total_area: 110, fire_safety_status: 'OK' },
  },
  {
    id: '2',
    rank: 2,
    style: 'Skandinavia',
    image_url: 'data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mP8z8BQDwAEhQGAhKmMIQAAAABJRU5ErkJggg==',
    scores: { composite: 0.75 },
    energy: { EUI: 100, total_area: 115, fire_safety_status: 'OK' },
  },
];

describe('OutputGallery Component', () => {
  it('harus merender gambar dari Base64', () => {
    const mockClick = vi.fn(); // ganti jest.fn() => vi.fn()
    render(<OutputGallery results={dummyResults} onCardClick={mockClick} />);

    const images = screen.getAllByRole('img');
    expect(images.length).toBe(2);
    expect(images[0]).toHaveAttribute('src', dummyResults[0].image_url);
  });

  it('harus memanggil onCardClick saat kartu diklik', () => {
    const mockClick = vi.fn(); // ganti jest.fn() => vi.fn()
    render(<OutputGallery results={dummyResults} onCardClick={mockClick} />);

    const styleText = screen.getByText('Modern');
    const card = styleText.closest('.result-card');
    fireEvent.click(card);

    expect(mockClick).toHaveBeenCalledWith(dummyResults[0]);
  });
});