export const getAuthToken = () => {
  if (typeof window === 'undefined') return ''

  try {
    const authData = JSON.parse(localStorage.getItem('authData') || '{}')
    return authData.token || ''
  } catch {
    return ''
  }
}

export const authHeaders = (headers: Record<string, string> = {}) => {
  const token = getAuthToken()
  return {
    ...headers,
    ...(token ? { Authorization: `Bearer ${token}` } : {})
  }
}

export const authFetch = (input: RequestInfo | URL, init: RequestInit = {}) =>
  fetch(input, {
    ...init,
    headers: authHeaders((init.headers || {}) as Record<string, string>)
  })
