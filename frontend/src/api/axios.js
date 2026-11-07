import axios from 'axios'

const API_BASE_URL =
  import.meta.env.VITE_API_URL || 'http://localhost:8000/api/v1'
const ACCESS_TOKEN_KEY = 'nuam_access_token'
const REFRESH_TOKEN_KEY = 'nuam_refresh_token'

export const api = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
})

const refreshClient = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
})

export function getAccessToken() {
  return localStorage.getItem(ACCESS_TOKEN_KEY)
}

export function getRefreshToken() {
  return localStorage.getItem(REFRESH_TOKEN_KEY)
}

export function saveTokens({ access_token, refresh_token }) {
  localStorage.setItem(ACCESS_TOKEN_KEY, access_token)
  localStorage.setItem(REFRESH_TOKEN_KEY, refresh_token)
}

export function clearTokens() {
  localStorage.removeItem(ACCESS_TOKEN_KEY)
  localStorage.removeItem(REFRESH_TOKEN_KEY)
}

api.interceptors.request.use((config) => {
  const accessToken = getAccessToken()

  if (accessToken) {
    config.headers.Authorization = `Bearer ${accessToken}`
  }

  return config
})

let refreshPromise = null
let onTokensRefreshed = null

export function setTokensRefreshedListener(listener) {
  onTokensRefreshed = listener
  return () => {
    if (onTokensRefreshed === listener) onTokensRefreshed = null
  }
}

function refreshAccessToken() {
  if (!refreshPromise) {
    const refreshToken = getRefreshToken()

    if (!refreshToken) {
      return Promise.reject(new Error('No existe un refresh token.'))
    }

    refreshPromise = refreshClient
      .post('/auth/refresh', { refresh_token: refreshToken })
      .then(({ data }) => {
        saveTokens(data)
        onTokensRefreshed?.(data.access_token)
        return data.access_token
      })
      .finally(() => {
        refreshPromise = null
      })
  }

  return refreshPromise
}

api.interceptors.response.use(
  (response) => response,
  async (error) => {
    const originalRequest = error.config
    const isUnauthorized = error.response?.status === 401
    const isRefreshRequest = originalRequest?.url?.endsWith('/auth/refresh')

    if (!isUnauthorized || !originalRequest || originalRequest._retry) {
      return Promise.reject(error)
    }

    if (isRefreshRequest) {
      clearTokens()
      return Promise.reject(error)
    }

    originalRequest._retry = true

    try {
      const accessToken = await refreshAccessToken()
      originalRequest.headers.Authorization = `Bearer ${accessToken}`
      return api(originalRequest)
    } catch (refreshError) {
      clearTokens()
      return Promise.reject(refreshError)
    }
  },
)

export default api
