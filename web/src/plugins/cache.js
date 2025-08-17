const sessionCache = {
  set(key, value) {
    if (!sessionStorage) {
      return
    }
    if (key != null && value != null) {
      sessionStorage.setItem(key, value)
    }
  },
  get(key) {
    if (!sessionStorage) {
      return null
    }
    if (key == null) {
      return null
    }
    return sessionStorage.getItem(key)
  },
  setJSON(key, jsonValue) {
    if (jsonValue != null) {
      this.set(key, JSON.stringify(jsonValue))
    }
  },
  getJSON(key) {
    const value = this.get(key)
    if (value != null) {
      try {
        return JSON.parse(value)
      } catch (e) {
        return null
      }
    }
  },
  remove(key) {
    if (!sessionStorage) {
      return
    }
    sessionStorage.removeItem(key)
  },
  clear() {
    if (!sessionStorage) {
      return
    }
    sessionStorage.clear()
  }
}

const localCache = {
  set(key, value) {
    if (!localStorage) {
      return
    }
    if (key != null && value != null) {
      localStorage.setItem(key, value)
    }
  },
  get(key) {
    if (!localStorage) {
      return null
    }
    if (key == null) {
      return null
    }
    return localStorage.getItem(key)
  },
  setJSON(key, jsonValue) {
    if (jsonValue != null) {
      this.set(key, JSON.stringify(jsonValue))
    }
  },
  getJSON(key) {
    const value = this.get(key)
    if (value != null) {
      try {
        return JSON.parse(value)
      } catch (e) {
        return null
      }
    }
  },
  remove(key) {
    if (!localStorage) {
      return
    }
    localStorage.removeItem(key)
  },
  clear() {
    if (!localStorage) {
      return
    }
    localStorage.clear()
  }
}

const memoryCache = {
  cache: {},
  set(key, value, expire) {
    this.cache[key] = {
      value,
      expire: expire ? new Date().getTime() + expire * 1000 : null
    }
  },
  get(key) {
    const cached = this.cache[key]
    if (!cached) {
      return null
    }
    if (cached.expire && cached.expire < new Date().getTime()) {
      this.remove(key)
      return null
    }
    return cached.value
  },
  setJSON(key, jsonValue, expire) {
    this.set(key, jsonValue, expire)
  },
  getJSON(key) {
    return this.get(key)
  },
  remove(key) {
    delete this.cache[key]
  },
  clear() {
    this.cache = {}
  }
}

export default {
  /**
   * 会话级缓存
   */
  session: sessionCache,
  /**
   * 本地缓存
   */
  local: localCache,
  /**
   * 内存级缓存
   */
  memory: memoryCache
}
