function goToModule(page) {
  window.location.href = page;
}

function updateHeaderUser(me) {
  const username = document.getElementById('username');
  const avatar = document.getElementById('user-avatar');
  const displayName = me.name || me.email || '用户';
  if (username) username.textContent = displayName;
  if (avatar) avatar.textContent = displayName.charAt(0).toUpperCase();
}

async function loadCurrentUser() {
  const profile = await API.get(`/api/users/profile?t=${Date.now()}`, {
    headers: { 'Cache-Control': 'no-cache', Authorization: `Bearer ${Auth.state.access}` },
  });
  const me = await API.get('/api/users/me', {
    headers: { Authorization: `Bearer ${Auth.state.access}` },
  });
  window.__ME__ = { ...me, ...profile };
}

async function ensureAuthAndLoad() {
  if (!Auth.state.access) {
    window.location.href = 'index.html';
    return;
  }

  try {
    await loadCurrentUser();
    refreshProfilePopover();
  } catch (err) {
    try {
      await Auth.refresh();
      await loadCurrentUser();
      refreshProfilePopover();
    } catch (refreshErr) {
      Auth.signOut();
      window.location.href = 'index.html';
    }
  }
}

function refreshProfilePopover() {
  const el = document.getElementById('profile-basic');
  if (!el || !window.__ME__) return;

  const me = window.__ME__;
  el.innerHTML = `
    <div>姓名：${me.name || ''}</div>
    <div>账号：${me.email || ''}</div>
    <div>学号：${me.student_id || ''}</div>
    <div>年级：${me.grade || ''}</div>
    <div>班级：${me.class_name || ''}</div>
  `;

  updateHeaderUser(me);

  const teacherModules = document.querySelectorAll('.teacher-only');
  teacherModules.forEach((module) => {
    module.style.display = me.role === 'teacher' ? 'flex' : 'none';
  });
}

function toggleProfile(force) {
  const popover = document.getElementById('profile-popover');
  if (!popover) return;

  if (typeof force === 'boolean') {
    popover.style.display = force ? 'block' : 'none';
    return;
  }

  popover.style.display = popover.style.display === 'none' ? 'block' : 'none';
}

document.addEventListener('DOMContentLoaded', () => {
  ensureAuthAndLoad();

  const profileBtn = document.getElementById('profile-btn');
  const popover = document.getElementById('profile-popover');

  if (profileBtn) {
    profileBtn.addEventListener('click', (event) => {
      event.stopPropagation();
      toggleProfile();
    });
  }

  if (popover) {
    popover.addEventListener('click', (event) => {
      event.stopPropagation();
    });
  }

  document.addEventListener('click', () => toggleProfile(false));

  const activeCards = document.querySelectorAll('.hub-module-card[data-target]');
  activeCards.forEach((card) => {
    card.tabIndex = 0;
    card.addEventListener('click', () => {
      goToModule(card.dataset.target);
    });
    card.addEventListener('keydown', (event) => {
      if (event.key === 'Enter' || event.key === ' ') {
        event.preventDefault();
        goToModule(card.dataset.target);
      }
    });
  });
});
