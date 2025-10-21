// 学生管理模块

let allStudents = [];
let currentStudentDetail = null;

// 页面加载时初始化
document.addEventListener('DOMContentLoaded', async function() {
  // 检查登录状态和权限
  try {
    // 先等待认证检查完成
    await Auth.checkAuth();
    
    // 检查是否登录
    if (!Auth.state.token || !Auth.state.user) {
      alert('请先登录');
      location.href = 'index.html';
      return;
    }
    
    // 检查是否为教师
    if (Auth.state.user.role !== 'teacher') {
      alert('权限不足，仅教师可访问');
      location.href = 'dashboard.html';
      return;
    }
    
    // 加载学生列表
    loadStudents();
    
    // 绑定搜索事件
    const searchInput = document.getElementById('search-input');
    if (searchInput) {
      searchInput.addEventListener('input', handleSearch);
    }
  } catch (error) {
    console.error('认证失败:', error);
    alert('请先登录');
    location.href = 'index.html';
  }

  // 点击弹窗外部关闭
  const modal = document.getElementById('student-modal');
  if (modal) {
    modal.addEventListener('click', function(e) {
      if (e.target === modal) {
        closeModal();
      }
    });
  }
});

// 加载学生列表
async function loadStudents() {
  const listContainer = document.getElementById('students-list');
  
  try {
    const response = await fetch('http://127.0.0.1:5000/api/users/students', {
      method: 'GET',
      headers: {
        'Authorization': `Bearer ${Auth.state.access}`,
        'Content-Type': 'application/json'
      }
    });

    if (!response.ok) {
      throw new Error('获取学生列表失败');
    }

    const data = await response.json();
    allStudents = data.students || [];
    
    renderStudents(allStudents);
  } catch (error) {
    console.error('加载学生列表失败:', error);
    listContainer.innerHTML = `
      <div class="empty-state">
        <div class="empty-state-icon">⚠️</div>
        <div>加载失败：${error.message}</div>
      </div>
    `;
  }
}

// 渲染学生列表
function renderStudents(students) {
  const listContainer = document.getElementById('students-list');
  
  if (!students || students.length === 0) {
    listContainer.innerHTML = `
      <div class="empty-state">
        <div class="empty-state-icon">👤</div>
        <div>暂无学生数据</div>
      </div>
    `;
    return;
  }

  listContainer.className = 'students-grid';
  listContainer.innerHTML = students.map(student => `
    <div class="student-card" onclick="openStudentDetail(${student.id})">
      <div class="student-header">
        <div class="student-avatar">${getInitials(student.name)}</div>
        <div class="student-info">
          <div class="student-name">${escapeHtml(student.name)}</div>
          <div class="student-id">${escapeHtml(student.student_id || '未设置学号')}</div>
        </div>
      </div>
      <div class="student-details">
        <div>📧 ${escapeHtml(student.email)}</div>
        <div>📚 年级：${escapeHtml(student.grade || '未设置')}</div>
        <div>🏫 班级：${escapeHtml(student.class_name || '未设置')}</div>
      </div>
      <div class="student-stats">
        <span>📁 ${student.document_count || 0} 个文档</span>
        <span>🕐 ${formatDate(student.created_at)}</span>
      </div>
    </div>
  `).join('');
}

// 搜索处理
function handleSearch(e) {
  const searchTerm = e.target.value.toLowerCase().trim();
  
  if (!searchTerm) {
    renderStudents(allStudents);
    return;
  }

  const filteredStudents = allStudents.filter(student => {
    return (
      (student.name && student.name.toLowerCase().includes(searchTerm)) ||
      (student.student_id && student.student_id.toLowerCase().includes(searchTerm)) ||
      (student.email && student.email.toLowerCase().includes(searchTerm)) ||
      (student.class_name && student.class_name.toLowerCase().includes(searchTerm)) ||
      (student.grade && student.grade.toLowerCase().includes(searchTerm))
    );
  });

  renderStudents(filteredStudents);
}

// 打开学生详情
async function openStudentDetail(studentId) {
  const modal = document.getElementById('student-modal');
  modal.classList.add('active');
  
  // 显示加载状态
  document.getElementById('modal-student-name').textContent = '加载中...';
  
  try {
    const response = await fetch(`http://127.0.0.1:5000/api/users/students/${studentId}`, {
      method: 'GET',
      headers: {
        'Authorization': `Bearer ${Auth.state.access}`,
        'Content-Type': 'application/json'
      }
    });

    if (!response.ok) {
      throw new Error('获取学生详情失败');
    }

    const data = await response.json();
    currentStudentDetail = data;
    
    renderStudentDetail(data);
  } catch (error) {
    console.error('加载学生详情失败:', error);
    alert('加载学生详情失败：' + error.message);
    closeModal();
  }
}

// 渲染学生详情
function renderStudentDetail(data) {
  const student = data.student;
  const documents = data.documents || [];

  // 头部信息
  document.getElementById('modal-avatar').textContent = getInitials(student.name);
  document.getElementById('modal-student-name').textContent = student.name;
  document.getElementById('modal-student-id').textContent = `学号：${student.student_id || '未设置'}`;
  document.getElementById('modal-student-email').textContent = `邮箱：${student.email}`;

  // 基本信息
  document.getElementById('detail-name').textContent = student.name;
  document.getElementById('detail-student-id').textContent = student.student_id || '未设置';
  document.getElementById('detail-grade').textContent = student.grade || '未设置';
  document.getElementById('detail-class').textContent = student.class_name || '未设置';
  document.getElementById('detail-email').textContent = student.email;
  document.getElementById('detail-created').textContent = formatDateTime(student.created_at);

  // 文档列表
  document.getElementById('doc-count').textContent = documents.length;
  const docsList = document.getElementById('documents-list');
  
  if (documents.length === 0) {
    docsList.innerHTML = `
      <div class="empty-state">
        <div class="empty-state-icon">📄</div>
        <div>该学生尚未上传任何文档</div>
      </div>
    `;
  } else {
    docsList.innerHTML = documents.map(doc => `
      <div class="document-item">
        <div class="document-icon">${getFileIcon(doc.file_type)}</div>
        <div class="document-info">
          <div class="document-name">${escapeHtml(doc.name)}</div>
          <div class="document-meta">
            ${escapeHtml(doc.category)} · ${formatFileSize(doc.file_size)} · ${formatDateTime(doc.created_at)}
          </div>
        </div>
      </div>
    `).join('');
  }
}

// 关闭弹窗
function closeModal() {
  const modal = document.getElementById('student-modal');
  modal.classList.remove('active');
  currentStudentDetail = null;
}

// 工具函数：获取首字母
function getInitials(name) {
  if (!name) return 'S';
  return name.charAt(0).toUpperCase();
}

// 工具函数：HTML转义
function escapeHtml(text) {
  if (!text) return '';
  const div = document.createElement('div');
  div.textContent = text;
  return div.innerHTML;
}

// 工具函数：格式化日期
function formatDate(dateString) {
  if (!dateString) return '未知';
  const date = new Date(dateString);
  const now = new Date();
  const diff = now - date;
  const days = Math.floor(diff / (1000 * 60 * 60 * 24));
  
  if (days === 0) return '今天';
  if (days === 1) return '昨天';
  if (days < 7) return `${days}天前`;
  if (days < 30) return `${Math.floor(days / 7)}周前`;
  if (days < 365) return `${Math.floor(days / 30)}月前`;
  return `${Math.floor(days / 365)}年前`;
}

// 工具函数：格式化日期时间
function formatDateTime(dateString) {
  if (!dateString) return '未知';
  const date = new Date(dateString);
  const year = date.getFullYear();
  const month = String(date.getMonth() + 1).padStart(2, '0');
  const day = String(date.getDate()).padStart(2, '0');
  const hours = String(date.getHours()).padStart(2, '0');
  const minutes = String(date.getMinutes()).padStart(2, '0');
  return `${year}-${month}-${day} ${hours}:${minutes}`;
}

// 工具函数：格式化文件大小
function formatFileSize(bytes) {
  if (!bytes || bytes === 0) return '0 B';
  const k = 1024;
  const sizes = ['B', 'KB', 'MB', 'GB'];
  const i = Math.floor(Math.log(bytes) / Math.log(k));
  return Math.round(bytes / Math.pow(k, i) * 100) / 100 + ' ' + sizes[i];
}

// 工具函数：获取文件图标
function getFileIcon(fileType) {
  if (!fileType) return '📄';
  const type = fileType.toLowerCase();
  if (type.includes('pdf')) return '📕';
  if (type.includes('doc') || type.includes('word')) return '📘';
  if (type.includes('xls') || type.includes('excel')) return '📗';
  if (type.includes('ppt') || type.includes('powerpoint')) return '📙';
  if (type.includes('image') || type.includes('jpg') || type.includes('png')) return '🖼️';
  if (type.includes('zip') || type.includes('rar')) return '📦';
  return '📄';
}

