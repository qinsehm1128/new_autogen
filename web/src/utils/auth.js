const TokenKey = 'Admin-Token'

export function getToken() {
  return localStorage.getItem(TokenKey)
}

export function setToken(token) {
  return localStorage.setItem(TokenKey, token)
}

export function removeToken() {
  return localStorage.removeItem(TokenKey)
}

// 获取用户信息
export function getUserInfo() {
  const userInfo = localStorage.getItem('userInfo')
  return userInfo ? JSON.parse(userInfo) : null
}

// 设置用户信息
export function setUserInfo(userInfo) {
  return localStorage.setItem('userInfo', JSON.stringify(userInfo))
}

// 移除用户信息
export function removeUserInfo() {
  return localStorage.removeItem('userInfo')
}

// 检查是否已登录
export function isLoggedIn() {
  return !!getToken()
}

// 清除所有认证信息
export function clearAuth() {
  removeToken()
  removeUserInfo()
}
