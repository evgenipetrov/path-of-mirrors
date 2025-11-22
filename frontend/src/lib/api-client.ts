import Axios, { type AxiosRequestConfig } from 'axios'

export const AXIOS_INSTANCE = Axios.create({
  baseURL: import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000',
  headers: {
    'Content-Type': 'application/json',
  },
})

// Add request interceptor for auth tokens if needed
AXIOS_INSTANCE.interceptors.request.use(
  (config) => {
    // Add auth token here if needed
    // const token = getAuthToken()
    // if (token) {
    //   config.headers.Authorization = `Bearer ${token}`
    // }
    return config
  },
  (error) => {
    return Promise.reject(error)
  }
)

// Add response interceptor for error handling
AXIOS_INSTANCE.interceptors.response.use(
  (response) => response,
  (error) => {
    // Global error handling can be added here
    return Promise.reject(error)
  }
)

// API client compatible with orval-generated code
// Accepts AxiosRequestConfig and returns data from response
export const apiClient = <T>(
  config: AxiosRequestConfig,
  options?: AxiosRequestConfig
): Promise<T> => {
  const source = Axios.CancelToken.source()

  // Merge config with options and add cancel token
  const axiosConfig: AxiosRequestConfig = {
    ...config,
    ...options,
    cancelToken: source.token,
  }

  const promise = AXIOS_INSTANCE(axiosConfig).then(({ data }) => data)

  // @ts-expect-error - adding cancel method to promise for TanStack Query cancellation support
  promise.cancel = () => {
    source.cancel('Query was cancelled')
  }

  return promise
}

export default apiClient
