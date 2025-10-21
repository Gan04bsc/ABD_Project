const Auth = {
  state: {
    access: sessionStorage.getItem('access_token') || '',
    refresh: sessionStorage.getItem('refresh_token') || '',
    role: sessionStorage.getItem('user_role') || '',
    userInfo: JSON.parse(sessionStorage.getItem('user_info') || '{}'),
  },
  setTokens({ access_token, refresh_token, role, user_info }) {
    if (access_token) {
      this.state.access = access_token;
      sessionStorage.setItem('access_token', access_token);
    }
    if (refresh_token) {
      this.state.refresh = refresh_token;
      sessionStorage.setItem('refresh_token', refresh_token);
    }
    if (role) {
      this.state.role = role;
      sessionStorage.setItem('user_role', role);
    }
    if (user_info) {
      this.state.userInfo = user_info;
      sessionStorage.setItem('user_info', JSON.stringify(user_info));
    }
    this.updateStatus();
  },
  signOut() {
    this.state.access = '';
    this.state.refresh = '';
    this.state.role = '';
    this.state.userInfo = {};
    sessionStorage.removeItem('access_token');
    sessionStorage.removeItem('refresh_token');
    sessionStorage.removeItem('user_role');
    sessionStorage.removeItem('user_info');
    this.updateStatus();
  },
  async submitRegister(e) {
    e.preventDefault();
    const form = e.target;
    const body = {
      email: form.email.value.trim(),
      name: form.name.value.trim(),
      password: form.password.value,
      role: form.role.value,
    };
    try {
      const res = await API.post('/api/auth/register', body);
      alert('注册成功，去登录试试');
    } catch (err) {
      alert('注册失败：' + err.message);
    }
    return false;
  },
  async submitLogin(e) {
    e.preventDefault();
    const form = e.target;
    const body = {
      email: form.email.value.trim(),
      password: form.password.value,
    };
    try {
      const res = await API.post('/api/auth/login', body);
      this.setTokens(res);
      
      // 获取用户详细信息
      try {
        const userInfo = await API.get('/api/users/me', {
          headers: { Authorization: `Bearer ${res.access_token}` },
        });
        this.setTokens({ user_info: userInfo });
      } catch (err) {
        console.log('获取用户信息失败，使用默认信息');
      }
      
      // 登录成功后跳转到主界面
      window.location.href = 'dashboard.html';
    } catch (err) {
      alert('登录失败：' + err.message);
    }
    return false;
  },
  async refresh() {
    if (!this.state.refresh) throw new Error('无 refresh token');
    const res = await API.post('/api/auth/refresh', null, {
      headers: { Authorization: `Bearer ${this.state.refresh}` },
    });
    this.setTokens(res);
    return res;
  },
  async me() {
    try {
      const res = await API.get('/api/users/me', {
        headers: { Authorization: `Bearer ${this.state.access}` },
      });
      alert('当前用户：' + JSON.stringify(res));
    } catch (err) {
      // 若 access 过期，尝试刷新
      if (this.state.refresh) {
        try {
          await this.refresh();
          const res = await API.get('/api/users/me', {
            headers: { Authorization: `Bearer ${this.state.access}` },
          });
          alert('当前用户：' + JSON.stringify(res));
          return;
        } catch {}
      }
      alert('获取用户失败：' + err.message);
    }
  },
  updateStatus() {
    const el = document.getElementById('auth-status');
    if (!el) return;
    if (this.state.access) {
      const roleText = this.state.role === 'teacher' ? '老师' : '学生';
      el.innerHTML = `已登录 (${roleText})`;
    } else {
      el.innerText = '未登录';
    }
  },
  
  // 检查认证状态（用于其他页面）
  async checkAuth() {
    // 如果没有 access token，直接失败
    if (!this.state.access) {
      throw new Error('未登录');
    }
    
    // 尝试获取用户信息验证 token 是否有效
    try {
      const userInfo = await API.get('/api/users/me', {
        headers: { Authorization: `Bearer ${this.state.access}` },
      });
      
      // 更新用户信息
      this.state.userInfo = userInfo;
      this.state.role = userInfo.role;
      sessionStorage.setItem('user_info', JSON.stringify(userInfo));
      sessionStorage.setItem('user_role', userInfo.role);
      
      // 为了兼容，添加 token 和 user 属性
      this.state.token = this.state.access;
      this.state.user = userInfo;
      
      return userInfo;
    } catch (err) {
      // 如果 access token 过期，尝试刷新
      if (this.state.refresh) {
        try {
          await this.refresh();
          // 刷新成功后重新获取用户信息
          const userInfo = await API.get('/api/users/me', {
            headers: { Authorization: `Bearer ${this.state.access}` },
          });
          
          this.state.userInfo = userInfo;
          this.state.role = userInfo.role;
          sessionStorage.setItem('user_info', JSON.stringify(userInfo));
          sessionStorage.setItem('user_role', userInfo.role);
          
          // 为了兼容，添加 token 和 user 属性
          this.state.token = this.state.access;
          this.state.user = userInfo;
          
          return userInfo;
        } catch (refreshErr) {
          // 刷新失败，清除认证信息
          this.signOut();
          throw new Error('登录已过期，请重新登录');
        }
      }
      
      // 没有 refresh token，清除认证信息
      this.signOut();
      throw new Error('登录已过期，请重新登录');
    }
  },
};

document.addEventListener('DOMContentLoaded', () => Auth.updateStatus());
