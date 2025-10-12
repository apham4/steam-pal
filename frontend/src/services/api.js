import axios from 'axios';
import { API_BASE_URL } from '../config';
import { useUserStore } from '../stores/user'

// Toggle this to switch between mock and real API
const MOCK_AUTH = false;
const MOCK_RECOMMENDATIONS = true;
const MOCK_AUDIT = true;

// Axios instance for real API
const api = axios.create({
  baseURL: API_BASE_URL, // The address of your FastAPI server
  headers: {
    'Content-Type': 'application/json',
  },
});

// Add JWT token to Authorization header for every request
api.interceptors.request.use(config => {
  const userStore = useUserStore()
  const token = userStore.jwt
  if (token) {
    config.headers.Authorization = `Bearer ${token}`
  }
  return config;
});

// # region Exported API functions
export function getSteamLoginUrl() {
  return MOCK_AUTH ? mockGetSteamLoginUrl() : realGetSteamLoginUrl()
}

export function getCurrentUser() {
  return MOCK_AUTH ? mockGetCurrentUser() : realGetCurrentUser()
}

export function logOut() {
  return MOCK_AUTH ? mockLogOut() : realLogOut()
}

export function getRecommendation(params) {
  return MOCK_RECOMMENDATIONS ? mockGetRecommendation(params) : realGetRecommendation(params);
}

export function getPastRecommendations() {
  return MOCK_RECOMMENDATIONS ? mockGetPastRecommendations() : realGetPastRecommendations();
}

export function updatePreferences(preferences) {
  return MOCK_RECOMMENDATIONS ? mockUpdatePreferences(preferences) : realUpdatePreferences(preferences);
}

export function logUserLogin() {
  return MOCK_AUDIT ? Promise.resolve({ success: true }) : realLogUserLogin();
}

export function logRecommendationRequest() {
  return MOCK_AUDIT ? Promise.resolve({ success: true }) : realLogRecommendationRequest();
}

export function logRecommendationActionTaken(actionType, recommendationId) {
  return MOCK_AUDIT ? Promise.resolve({ success: true }) : realLogRecommendationActionTaken(actionType, recommendationId);
}
// # endregion

// #region Mock Implementations
// Simulate network delay
function delay(ms) {
  return new Promise(resolve => setTimeout(resolve, ms));
}

// Mock game data
const mockGames = [
  {
    id: '1',
    title: 'Portal 2',
    thumbnail: 'https://cdn.cloudflare.steamstatic.com/steam/apps/620/header.jpg',
    releaseDate: '2011-04-19',
    publisher: 'Valve',
    developer: 'Valve',
    price: '$9.99',
    salePrice: '$4.99',
    description: 'The highly anticipated sequel to Portal...',
  },
  // Add more mock games as needed
];

// Mock Steam login URL
async function mockGetSteamLoginUrl() {
  await delay(200)
  return 'https://steamcommunity.com/openid/login?mock=true'
}

// Mock current user profile
async function mockGetCurrentUser() {
  await delay(200)
  return {
    steam_id: '12345678901234567',
    display_name: 'Mock User',
    avatar_url: 'https://steamcdn-a.akamaihd.net/steamcommunity/public/images/avatars/ab/abcdef1234567890.jpg',
    profile_url: 'https://steamcommunity.com/profiles/12345678901234567',
    last_login: '2025-10-07T12:00:00Z'
  }
}

async function mockLogOut() {
  await delay(100);
  return { success: true };
}

// Mock get AI recommendation
async function mockGetRecommendation({ genre, useWishlist }) {
  await delay(700);
  // Filter out games already liked/disliked/past (simulate logic)
  return {
    game: mockGames[0],
    reasoning: 'Based on your preferences, Portal 2 is a great fit for you.',
  };
}

// Mock get past recommendations
async function mockGetPastRecommendations() {
  await delay(300);
  return [];
}

// Mock update liked/disliked/past recommendations
async function mockUpdatePreferences({ liked, disliked, pastRecommendations }) {
  await delay(200);
  return { success: true };
}

// #endregion

// #region Real API Implementations
async function realGetSteamLoginUrl() {
  const res = await api.get('/api/auth/steam/login')
  return res.data.login_url
}

async function realGetCurrentUser() {
  const res = await api.get('/api/auth/me')
  return res.data
}

async function realLogOut() {
  const res = await api.post('/api/auth/logout')
  return res.data
}

async function realGetRecommendation(params) {
  const res = await api.post('/api/recommendations', params);
  return res.data;
}

async function realGetPastRecommendations() {
  const res = await api.get('/api/recommendations/history');
  return res.data;
}

async function realUpdatePreferences({ liked, disliked, pastRecommendations }) {
  const res = await api.post('/api/preferences/update', { liked, disliked, pastRecommendations });
  return { success: true };
}

async function realLogUserLogin() {
  const userId = useUserStore()?.profile?.steam_id;
  const timestamp = new Date().toISOString();

  if (!userId) {
    throw new Error('Missing userId (steam_id) in user store profile');
  }

  const res = await api.post('/api/admin/events/logins', {
    userId,
    timestamp,
  });
  return res.data;
}

async function realLogRecommendationRequest() {
  const userId = useUserStore()?.profile?.steam_id;
  const timestamp = new Date().toISOString();

  if (!userId) {
    throw new Error('Missing userId (steam_id) in user store profile');
  }

  const res = await api.post('/api/admin/events/recommendations', {
    userId,
    timestamp,
  });
  return res.data;
}

async function realLogRecommendationActionTaken(actionType, recommendationId) {
  const userId = useUserStore()?.profile?.steam_id;
  const timestamp = new Date().toISOString();

  if (!userId) {
    throw new Error('Missing userId (steam_id) in user store profile');
  }

  const res = await api.post('/api/admin/events/actions', {
    userId,
    actionType,
    recommendationId,
    timestamp,
  });
  return res.data;
}
// #endregion