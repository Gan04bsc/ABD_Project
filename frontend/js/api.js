const API = {
  baseURL: 'http://127.0.0.1:5000',

  async request(path, options = {}, _retried = false) {
    const url = this.baseURL + path;
    const { headers = {}, ...restOptions } = options;
    const config = {
      ...restOptions,
      headers: {
        'Content-Type': 'application/json',
        'Accept': 'application/json',
        ...headers,
      },
    };

    try {
      const response = await fetch(url, config);

      // 尝试安全解析 JSON（处理空响应或非 JSON 响应）
      let data = null;
      const contentType = response.headers.get('content-type') || '';
      if (contentType.includes('application/json')) {
        try { data = await response.json(); } catch { data = null; }
      } else {
        try { data = await response.json(); } catch { data = null; }
      }

      if (!response.ok) {
        const msg = (data && (data.error || data.message || data.msg)) || '请求失败';

        // 处理 401：尝试使用 refresh token 刷新并重试一次
        if (response.status === 401 && !_retried && typeof Auth !== 'undefined' && Auth.state && Auth.state.refresh) {
          try {
            await Auth.refresh();
            const nextHeaders = { ...config.headers };
            // 若原请求带有 Authorization 则更新为新的 access
            if (nextHeaders.Authorization || (typeof Auth.state.access === 'string' && Auth.state.access)) {
              nextHeaders.Authorization = `Bearer ${Auth.state.access}`;
            }
            return await this.request(path, { ...config, headers: nextHeaders }, true);
          } catch (_) {
            // 刷新失败，继续抛出原错误
          }
        }

        const error = new Error(msg);
        error.error = msg;
        error.data = data;
        error.status = response.status;
        throw error;
      }

      return data;
    } catch (err) {
      if (err && (err.error || err.message)) throw err;
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

