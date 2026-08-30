import axios from 'axios';

const API_BASE_URL = 'http://localhost:8000/api/v1';

export const generateFloorplan = async (location, userText) => {
  try {
    const response = await axios.post(`${API_BASE_URL}/generate`, {
      location,
      user_text: userText,
      weights: [0.25, 0.25, 0.25, 0.25],
    });
    return response.data; // { data, parsed_data }
  } catch (error) {
    if (error.response) {
      throw new Error(error.response.data.detail || 'Server error');
    }
    throw new Error('Network error');
  }
};