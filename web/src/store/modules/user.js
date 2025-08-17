import { defineStore } from 'pinia'
import { getToken, setToken, removeToken, setUserInfo, removeUserInfo } from '@/utils/auth'
import request from '@/utils/request'

const useUserStore = defineStore('user', {
  state: () => ({
    token: getToken(),
    name: '',
    avatar: '',
    roles: [],
    permissions: [],
    userInfo: {}
  }),

  getters: {
    isLoggedIn: (state) => !!state.token,
    hasRole: (state) => (role) => state.roles.includes(role),
    hasPermission: (state) => (permission) => state.permissions.includes(permission)
  },

  actions: {
    // 用户登录
    login(userInfo) {
      const username = userInfo.username.trim()
      const password = userInfo.password
      const code = userInfo.code
      const uuid = userInfo.uuid

      return new Promise((resolve, reject) => {
        request({
          url: '/login',
          method: 'post',
          data: {
            username,
            password,
            code,
            uuid
          }
        }).then(res => {
          setToken(res.token)
          this.token = res.token
          resolve()
        }).catch(error => {
          reject(error)
        })
      })
    },

    // 获取用户信息
    getInfo() {
      return new Promise((resolve, reject) => {
        request({
          url: '/getInfo',
          method: 'get'
        }).then(res => {
          const user = res.user
          const avatar = user.avatar === '' || user.avatar == null ? require('@/assets/images/profile.jpg') : user.avatar

          if (res.roles && res.roles.length > 0) {
            this.roles = res.roles
            this.permissions = res.permissions
          } else {
            this.roles = ['ROLE_DEFAULT']
          }

          this.name = user.userName
          this.avatar = avatar
          this.userInfo = user

          setUserInfo(user)
          resolve(res)
        }).catch(error => {
          reject(error)
        })
      })
    },

    // 用户登出
    logOut() {
      return new Promise((resolve, reject) => {
        request({
          url: '/logout',
          method: 'post'
        }).then(() => {
          this.token = ''
          this.roles = []
          this.permissions = []
          this.name = ''
          this.avatar = ''
          this.userInfo = {}

          removeToken()
          removeUserInfo()
          resolve()
        }).catch(error => {
          this.token = ''
          this.roles = []
          this.permissions = []
          this.name = ''
          this.avatar = ''
          this.userInfo = {}

          removeToken()
          removeUserInfo()
          reject(error)
        })
      })
    },

    // 前端登出
    fedLogOut() {
      return new Promise(resolve => {
        this.token = ''
        this.roles = []
        this.permissions = []
        this.name = ''
        this.avatar = ''
        this.userInfo = {}

        removeToken()
        removeUserInfo()
        resolve()
      })
    },

    // 设置用户信息
    setUserInfo(userInfo) {
      this.userInfo = userInfo
      this.name = userInfo.userName || userInfo.name
      setUserInfo(userInfo)
    },

    // 设置Token
    setToken(token) {
      this.token = token
      setToken(token)
    },

    // 设置角色
    setRoles(roles) {
      this.roles = roles
    },

    // 设置权限
    setPermissions(permissions) {
      this.permissions = permissions
    },

    // 重置状态
    resetState() {
      this.token = ''
      this.name = ''
      this.avatar = ''
      this.roles = []
      this.permissions = []
      this.userInfo = {}
    }
  }
})

export default useUserStore
