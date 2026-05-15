import { createContext, useContext, useEffect, useState } from 'react'
import api from '../lib/api'

const AuthContext = createContext(null)

export function AuthProvider({ children }) {
  const [user, setUser] = useState(() => {
    const raw = localStorage.getItem('ccrts_user')
    return raw ? JSON.parse(raw) : null
  })
  const [loading, setLoading] = useState(false)

  // On mount, if we have a token, verify it by hitting /auth/me — this
  // refreshes the cached user record and silently logs out on stale tokens.
  useEffect(() => {
    const token = localStorage.getItem('ccrts_token')
    if (!token) return
    api.get('/auth/me').then((res) => {
      setUser(res.data)
      localStorage.setItem('ccrts_user', JSON.stringify(res.data))
    }).catch(() => {})
  }, [])

  const login = async (email, password) => {
    setLoading(true)
    try {
      const { data } = await api.post('/auth/login', { email, password })
      localStorage.setItem('ccrts_token', data.access_token)
      localStorage.setItem('ccrts_user', JSON.stringify(data.user))
      setUser(data.user)
      return data.user
    } finally {
      setLoading(false)
    }
  }

  const register = async (payload) => {
    setLoading(true)
    try {
      const { data } = await api.post('/auth/register', payload)
      localStorage.setItem('ccrts_token', data.access_token)
      localStorage.setItem('ccrts_user', JSON.stringify(data.user))
      setUser(data.user)
      return data.user
    } finally {
      setLoading(false)
    }
  }

  const logout = () => {
    localStorage.removeItem('ccrts_token')
    localStorage.removeItem('ccrts_user')
    setUser(null)
  }

  const hasRole = (...roles) => user && roles.includes(user.role?.name)

  return (
    <AuthContext.Provider value={{ user, loading, login, register, logout, hasRole }}>
      {children}
    </AuthContext.Provider>
  )
}

export const useAuth = () => useContext(AuthContext)
