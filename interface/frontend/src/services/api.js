import axios from 'axios';

const API_BASE_URL = 'http://localhost:8000';

export const generateFloorplan = async (userText, weights, coordinates) => {
  const payload = {
    user_text: userText,
    location: coordinates, // { lat, lng }
  };
  
  const response = await axios.post(`${API_BASE_URL}/generate`, payload);
  return response.data; // { data: [...], parsed_data: {...} }
};