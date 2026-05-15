import axios from 'axios'
import { Message } from '@arco-design/web-vue'

const http = axios.create({
  baseURL: '/api',
  timeout: 30000,
})

// 响应拦截：统一处理后端 {"code": 200, "data": ..., "msg": "..."} 格式
http.interceptors.response.use(
  (response) => {
    const { code, data, msg } = response.data
    if (code === 200) {
      return data
    }
    Message.error(msg || '请求失败')
    return Promise.reject(new Error(msg))
  },
  (error) => {
    const msg = error.response?.data?.msg || '网络请求异常'
    Message.error(msg)
    return Promise.reject(error)
  }
)

export default http
