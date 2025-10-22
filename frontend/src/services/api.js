import axios from 'axios';
import { API_BASE_URL } from '../config';
import { useUserStore } from '../stores/user'

// Toggle this to switch between mock and real API
const MOCK_AUTH = false;
const MOCK_RECOMMENDATIONS = false;
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

export function getRecommendationHistory(pageNum, pageSize) {
  return MOCK_RECOMMENDATIONS ? mockGetRecommendationHistory(pageNum, pageSize) : realGetRecommendationHistory(pageNum, pageSize);
}

export function likeGame(gameId) {
  return MOCK_RECOMMENDATIONS ? mockLikeGame(gameId) : realLikeGame(gameId);
}

export function dislikeGame(gameId) {
  return MOCK_RECOMMENDATIONS ? mockDislikeGame(gameId) : realDislikeGame(gameId);
}

export function removePreference(gameId) {
  return MOCK_RECOMMENDATIONS ? mockRemovePreference(gameId) : realRemovePreference(gameId);
}

export function getLikedGames() {
  return MOCK_RECOMMENDATIONS ? mockGetLikedGames() : realGetLikedGames();
}

export function getDislikedGames() {
  return MOCK_RECOMMENDATIONS ? mockGetDislikedGames() : realGetDislikedGames();
}

export function getAllPreferences() {
  return MOCK_RECOMMENDATIONS ? mockGetAllPreferences() : realGetAllPreferences();
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
    matchScore: 92
  };
}

// Mock get paginated recommendation history
async function mockGetRecommendationHistory(pageNum, pageSize) {
  await delay(200);
  return {
    recommendations: [mockGames[0], mockGames[0], mockGames[0]],
    currentPage: pageNum,
    pageSize: pageSize,
    totalRecommendations: 3,
    pages: 1,
  };
}

// Mock like a game
async function mockLikeGame(gameId) {
  await delay(100);
  return {
    status: "success",
    gameId: gameId,
    preference: "liked",
    message: `Game ${gameId} liked`
  };
}

// Mock remove a preference
async function mockRemovePreference(gameId) {
  await delay(100);
  return {
    status: "success",
    gameId: gameId,
    message: `Preference for game ${gameId} removed`
  };
}

// Mock get liked games
async function mockGetLikedGames() {
  await delay(100);
  return [mockGames[0], mockGames[0], mockGames[0]];
}

// Mock get disliked games
async function mockGetDislikedGames() {
  await delay(100);
  return [mockGames[0], mockGames[0], mockGames[0]];
}

// Mock dislike a game
async function mockDislikeGame(gameId) {
  await delay(100);
  return {
    status: "success",
    gameId: gameId,
    preference: "disliked",
    message: `Game ${gameId} disliked`
  };
}

// Mock get all preferences
async function mockGetAllPreferences() {
  await delay(100);
  return {
    preferences: {
      liked: [mockGames[0], mockGames[0], mockGames[0]],
      disliked: [mockGames[0], mockGames[0], mockGames[0]]
    },
    totals: {
      liked: 3,
      disliked: 3
    }
  };
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

async function realGetRecommendationHistory(pageNum, pageSize) {
  const res = await api.get('/api/recommendations/history', {
    params: { page: pageNum, limit: pageSize },
  });
  return {
    recommendations: res.data.recommendations,
    currentPage: res.data.page,
    pageSize: res.data.limit,
    totalRecommendations: res.data.total,
    pages: res.data.pages,
  };
}

async function realLikeGame(gameId) {
  const res = await api.post(`/api/preferences/${gameId}/like`);
  return res.data;
}

async function realDislikeGame(gameId) {
  const res = await api.post(`/api/preferences/${gameId}/dislike`);
  return res.data;
}

async function realRemovePreference(gameId) {
  const res = await api.delete(`/api/preferences/${gameId}`);
  return res.data;
}

async function realGetLikedGames() {
  const res = await api.get('/api/preferences/liked');
  return res.data.games;
}

async function realGetDislikedGames() {
  const res = await api.get('/api/preferences/disliked');
  return res.data.games;
}

async function realGetAllPreferences() {
  const res = await api.get('/api/preferences/all');
  return res.data;
  // res.data.preferences has liked and disliked arrays.
  // res.data.totals has liked and disliked counts.
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