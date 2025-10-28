import axios from 'axios';
import { API_BASE_URL } from '../../config';

// Axios instance for API
const api = axios.create({
  baseURL: API_BASE_URL, // The address of your FastAPI server
  headers: {
    'Content-Type': 'application/json',
  },
});

export const fetchUserEvents = async (params = {}) => {
  // params: { steamId, eventType, from, to }
  try {
    const query = new URLSearchParams();
    if (params.steamId) query.append('steamId', params.steamId);
    if (params.eventType) query.append('eventType', params.eventType); // comma-separated string
    if (params.from) query.append('from', params.from);
    if (params.to) query.append('to', params.to);

    const response = await api.get(`/api/events?${query.toString()}`);
    // Response shape: { events: [...] }
    return response.data.events || [];
  } catch (error) {
    console.error('Failed to fetch user events:', error);
    return [];
  }
};