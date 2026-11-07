import { useEffect, useMemo, useState } from 'react'
import api, {
  clearTokens,
  getAccessToken,
  saveTokens,
  setTokensRefreshedListener,
} from '../api/axios'
import { AuthContext } from './auth-context'

function decodeToken(token) {
  try {
    const payload = token.split('.')[1]
    const paddedPayload = payload.padEnd(payload.length + ((4 - (payload.length % 4)) % 4), '=')
    return JSON.parse(
      decodeURIComponent(
        window
          .atob(paddedPayload.replace(/-/g, '+').replace(/_/g, '/'))
          .split('')
          .map((char) => `%${`00${char.charCodeAt(0).toString(16)}`.slice(-2)}`)
          .join(''),
      ),
    )
  } catch {
    return null
  }
}

export function AuthProvider({ children }) {
  const [token, setToken] = useState(getAccessToken())
  const [user, setUser] = useState(() => {
    const currentToken = getAccessToken()
    return currentToken ? decodeToken(currentToken) : null
  })

  useEffect(() => setTokensRefreshedListener((nextToken) => {
    setToken(nextToken)
    setUser(decodeToken(nextToken))
  }), [])

  async function login(identificador, password) {
    const { data } = await api.post('/auth/login', { identificador, password })
    saveTokens(data)
    setToken(data.access_token)
    setUser(decodeToken(data.access_token))
    return data
  }

  function logout() {
    clearTokens()
    setToken(null)
    setUser(null)
  }

  const value = useMemo(
    () => ({ user, token, rol: user?.rol, login, logout }),
    [token, user],
  )

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>
}
