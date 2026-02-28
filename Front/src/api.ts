// Frontend API shim — frontend deprecated
// This module kept as a stub so imports don't break; calls will raise an error.

const deprecated = () => {
  throw new Error('Frontend API is deprecated in this repository. Use backend APIs directly.')
}

const api: any = {
  get: async () => deprecated(),
  post: async () => deprecated(),
  put: async () => deprecated(),
  delete: async () => deprecated(),
}

export default api
