import axios from 'axios';

const API_BASE = 'http://localhost:8000/api/v1';

export const generateFloorplan = async (coordinates, userText) => {
  const response = await fetch('http://localhost:8000/api/v1/generate', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
      userText: userText,
      weights: [0.25, 0.25, 0.25, 0.25],
      coordinates: coordinates
    })
  });
  if (!response.ok) {
    const err = await response.json().catch(() => ({}));
    throw new Error(err.detail || 'Generation failed');
  }
  return (await response.json()).data;
};