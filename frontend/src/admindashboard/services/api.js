import axios from 'axios';
import { API_BASE_URL } from '../../config';

// Toggle this to switch between mock and real API
const USE_MOCK = true;

// Axios instance for real API
const api = axios.create({
  baseURL: API_BASE_URL, // The address of your FastAPI server
  headers: {
    'Content-Type': 'application/json',
  },
});

// # region Exported API functions
// Fetch raw event data for a given type
export function fetchEvents({ dateRange, statType }) {
  return USE_MOCK ? mockFetchEvents({ dateRange, statType }) : realFetchEvents({ dateRange, statType });
}
// # endregion

// # region Mock Implementations 
// Simulate network delay
function delay(ms) {
  return new Promise(resolve => setTimeout(resolve, ms));
}

async function mockFetchEvents({ dateRange, statType }) {
  await delay(200);
  let key = '';
  switch ((statType || '').toLowerCase()) {
    case 'logins':
      key = 'logins';
      break;
    case 'recommendation requests':
    case 'recommendations':
      key = 'recommendations';
      break;
    case 'actions taken':
    case 'actions':
      key = 'actions';
      break;
    default:
      key = 'logins';
  }
  let data = mockEvents[key] || [];
  if (dateRange && dateRange.length === 2) {
    data = data.filter(d => d.timestamp >= dateRange[0] && d.timestamp <= dateRange[1]);
  }
  return data;
}

// Mock raw event data
const mockEvents = {
  logins: [
    { userId: '76561197960287930', timestamp: '2025-10-01T12:00:00Z' },
    { userId: '76561197960287930', timestamp: '2025-10-02T09:00:00Z' },
    { userId: '76561197960287930', timestamp: '2025-10-03T15:00:00Z' }
  ],
  recommendations: [
    { userId: '76561197960287930', timestamp: '2025-10-01T12:05:00Z' },
    { userId: '76561197960287930', timestamp: '2025-10-02T09:10:00Z' }
  ],
  actions: [
    { userId: '76561197960287930', actionType: 'like', recommendationId: 'abc123', timestamp: '2025-10-01T12:10:00Z' },
    { userId: '76561197960287930', actionType: 'view', recommendationId: 'abc123', timestamp: '2025-10-01T12:12:00Z' }
  ]
};
// # endregion

// # region Real Implementations
async function realFetchEvents({ dateRange, statType }) {
  try {
    let endpoint = '';
    switch ((statType || '').toLowerCase()) {
      case 'logins':
        endpoint = '/api/admin/events/logins';
        break;
      case 'recommendation requests':
      case 'recommendations':
        endpoint = '/api/admin/events/recommendations';
        break;
      case 'actions taken':
      case 'actions':
        endpoint = '/api/admin/events/actions';
        break;
      default:
        endpoint = '/api/admin/events/logins';
    }
    const params = {};
    if (dateRange && dateRange.length === 2) {
      params.start = dateRange[0];
      params.end = dateRange[1];
    }
    const res = await api.get(endpoint, { params });
    return res.data;
  } catch (err) {
    const msg = err?.response?.data?.detail || err?.message || 'Failed to fetch events';
    throw new Error(msg);
  }
}
// # endregion