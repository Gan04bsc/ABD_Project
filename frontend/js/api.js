const API = {
  baseURL: 'http://127.0.0.1:5000',
  
  async request(path, options = {}) {
    const url = this.baseURL + path;
    const config = {
      headers: {
        'Content-Type': 'application/json',
        ...(options.headers || {}),
      },
      ...options,
    };
    
    try {
      const response = await fetch(url, config);
      const data = await response.json();
      
      if (!response.ok) {
        const error = new Error(data.error || data.message || '请求失败');
        error.error = data.error || data.message || '请求失败';
        error.data = data;
        throw error;
      }
      
      return data;
    } catch (err) {
      if (err.error) throw err;
      if (err.message) throw err;
      throw new Error('网络请求失败');
    }
  },
  
  get(path, options = {}) {
    return this.request(path, { method: 'GET', ...options });
  },
  
  post(path, body = null, options = {}) {
    const config = { method: 'POST', ...options };
    if (body !== null) {
      config.body = JSON.stringify(body);
    }
    return this.request(path, config);
  },
  
  put(path, body = null, options = {}) {
    const config = { method: 'PUT', ...options };
    if (body !== null) {
      config.body = JSON.stringify(body);
    }
    return this.request(path, config);
  },
  
  patch(path, body = null, options = {}) {
    const config = { method: 'PATCH', ...options };
    if (body !== null) {
      config.body = JSON.stringify(body);
    }
    return this.request(path, config);
  },
  
  delete(path, options = {}) {
    return this.request(path, { method: 'DELETE', ...options });
  },
};

