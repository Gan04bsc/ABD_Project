const Auth = {
  state: {
    access: localStorage.getItem('access_token') || '',
    refresh: localStorage.getItem('refresh_token') || '',
    role: localStorage.getItem('user_role') || '',
    userInfo: JSON.parse(localStorage.getItem('user_info') || '{}'),
  },
  setTokens({ access_token, refresh_token, role, user_info }) {
    if (access_token) {
      this.state.access = access_token;
      localStorage.setItem('access_token', access_token);
    }
    if (refresh_token) {
      this.state.refresh = refresh_token;
      localStorage.setItem('refresh_token', refresh_token);
    }
    if (role) {
      this.state.role = role;
      localStorage.setItem('user_role', role);
    }
    if (user_info) {
      this.state.userInfo = user_info;
      localStorage.setItem('user_info', JSON.stringify(user_info));
    }
    this.updateStatus();
  },
  signOut() {
    this.state.access = '';
    this.state.refresh = '';
    this.state.role = '';
    this.state.userInfo = {};
    localStorage.removeItem('access_token');
    localStorage.removeItem('refresh_token');
    localStorage.removeItem('user_role');
    localStorage.removeItem('user_info');
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
};

document.addEventListener('DOMContentLoaded', () => Auth.updateStatus());
