// 导航功能
function goToModule(page) {
	window.location.href = page;
}

// 用户信息管理
async function ensureAuthAndLoad() {
	// 未登录则跳回登录页
	if (!Auth.state.access) {
		window.location.href = 'index.html';
		return;
	}
	try {
		// 统一使用 /api/users/profile 接口获取用户资料（加时间戳防缓存）
		const profile = await API.get(`/api/users/profile?t=${Date.now()}`, {
			headers: { 'Cache-Control': 'no-cache', Authorization: `Bearer ${Auth.state.access}` },
		});
		// 同时获取完整用户信息用于其他用途
		const me = await API.get('/api/users/me', {
			headers: { Authorization: `Bearer ${Auth.state.access}` },
		});
		// 合并数据
		window.__ME__ = { ...me, ...profile };
		await refreshProfilePopover();
	} catch (err) {
		// access 过期则刷新并重试
		try {
			await Auth.refresh();
			const profile = await API.get(`/api/users/profile?t=${Date.now()}`, {
				headers: { 'Cache-Control': 'no-cache', Authorization: `Bearer ${Auth.state.access}` },
			});
			const me2 = await API.get('/api/users/me', {
				headers: { Authorization: `Bearer ${Auth.state.access}` },
			});
			window.__ME__ = { ...me2, ...profile };
			await refreshProfilePopover();
		} catch (e) {
			window.location.href = 'index.html';
		}
	}
}

// 刷新用户信息弹层
async function refreshProfilePopover() {
	const el = document.getElementById('profile-basic');
	if (!el || !window.__ME__) return;
	const me = window.__ME__;
	el.innerHTML = `
		<div>姓名：${me.name || ''}</div>
		<div>学号：${me.student_id || ''}</div>
		<div>年级：${me.grade || ''}</div>
		<div>班级：${me.class_name || ''}</div>
	`;
	
	// 如果是教师，显示教师专属模块
	if (me.role === 'teacher') {
		const teacherModules = document.querySelectorAll('.teacher-only');
		teacherModules.forEach(module => {
			module.style.display = 'block';
		});
	}
}

// 切换用户信息弹层显示
function toggleProfile(force) {
	const p = document.getElementById('profile-popover');
	if (!p) return;
	if (typeof force === 'boolean') {
		p.style.display = force ? 'block' : 'none';
	} else {
		p.style.display = p.style.display === 'none' ? 'block' : 'none';
	}
}

// 页面加载时初始化
document.addEventListener('DOMContentLoaded', ensureAuthAndLoad);

// 绑定用户信息按钮事件
document.addEventListener('DOMContentLoaded', () => {
	const btn = document.getElementById('profile-btn');
	if (btn) btn.addEventListener('click', () => toggleProfile());
});

// 添加模块卡片的悬停效果
document.addEventListener('DOMContentLoaded', () => {
	const cards = document.querySelectorAll('.module-card');
	cards.forEach(card => {
		card.addEventListener('mouseenter', () => {
			card.style.boxShadow = '0 4px 12px rgba(0,0,0,0.15)';
		});
		card.addEventListener('mouseleave', () => {
			card.style.boxShadow = 'none';
		});
	});
});