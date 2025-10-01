import axios from 'axios';
import { API_BASE_URL } from '../config';

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
export function authenticateWithSteam() {
  return USE_MOCK ? mockAuthenticateWithSteam() : realAuthenticateWithSteam();
}

export function guestLogin(steamId) {
  return USE_MOCK ? mockGuestLogin(steamId) : realGuestLogin(steamId);
}

export function getRecommendation(params) {
  return USE_MOCK ? mockGetRecommendation(params) : realGetRecommendation(params);
}

export function getPastRecommendations(steamId) {
  return USE_MOCK ? mockGetPastRecommendations(steamId) : realGetPastRecommendations(steamId);
}

export function updatePreferences(preferences) {
  return USE_MOCK ? mockUpdatePreferences(preferences) : realUpdatePreferences(preferences);
}
// # endregion

// #region Mock Implementations
// Simulate network delay
function delay(ms) {
  return new Promise(resolve => setTimeout(resolve, ms));
}

// Mock user profile data
const mockProfile = {
  steamId: '12345678901234567',
  name: 'SteamUser',
  avatar: 'https://steamcdn-a.akamaihd.net/steamcommunity/public/images/avatars/ab/abcdef1234567890.jpg',
};

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

// Mock authentication (returns JWT and profile)
export async function mockAuthenticateWithSteam() {
  await delay(500);
  return {
    jwt: 'mock-jwt-token',
    profile: mockProfile,
    liked: [],
    disliked: [],
    pastRecommendations: [],
  };
}

// Mock guest login (returns profile with only Steam ID)
export async function mockGuestLogin(steamId) {
  await delay(300);
  return {
    profile: { steamId, name: 'Guest', avatar: '' },
    liked: [],
    disliked: [],
    pastRecommendations: [],
  };
}

// Mock get AI recommendation
export async function mockGetRecommendation({ steamId, genre, useWishlist }) {
  await delay(700);
  // Filter out games already liked/disliked/past (simulate logic)
  return {
    game: mockGames[0],
    reasoning: 'Based on your preferences, Portal 2 is a great fit for you.',
  };
}

// Mock get past recommendations
export async function mockGetPastRecommendations(steamId) {
  await delay(300);
  return [];
}

// Mock update liked/disliked/past recommendations
export async function mockUpdatePreferences({ steamId, liked, disliked, pastRecommendations }) {
  await delay(200);
  return { success: true };
}

// #endregion

// #region Real API Implementations
async function realAuthenticateWithSteam() {
  const res = await api.post('/auth/steam');
  return res.data;
}
async function realGuestLogin(steamId) {
  const res = await api.post('/auth/guest', { steamId });
  return res.data;
}
async function realGetRecommendation(params) {
  const res = await api.post('/recommendation', params);
  return res.data;
}

export async function realGetPastRecommendations(steamId) {
  const res = await api.post('/recommendation/past', { steamId });
  return res.data;
}

export async function realUpdatePreferences({ steamId, liked, disliked, pastRecommendations }) {
  const res = await api.post('/preferences/update', { steamId, liked, disliked, pastRecommendations });
  return { success: true };
}
// #endregion