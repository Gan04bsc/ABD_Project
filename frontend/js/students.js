let allStudents = [];

const state = {
  activeStudentId: null,
  detailRequestSeq: 0,
};

function getAuthHeaders() {
  return { Authorization: `Bearer ${Auth.state.access}` };
}

function escapeHtml(value) {
  const div = document.createElement("div");
  div.textContent = value == null ? "" : String(value);
  return div.innerHTML;
}

function formatDateTime(value) {
  if (!value) return "-";
  const date = new Date(value);
  if (Number.isNaN(date.getTime())) return "-";
  const yyyy = date.getFullYear();
  const mm = String(date.getMonth() + 1).padStart(2, "0");
  const dd = String(date.getDate()).padStart(2, "0");
  const hh = String(date.getHours()).padStart(2, "0");
  const mi = String(date.getMinutes()).padStart(2, "0");
  return `${yyyy}-${mm}-${dd} ${hh}:${mi}`;
}

function formatDateAgo(value) {
  if (!value) return "-";
  const date = new Date(value);
  if (Number.isNaN(date.getTime())) return "-";
  const days = Math.floor((Date.now() - date.getTime()) / (1000 * 60 * 60 * 24));
  if (days <= 0) return "今天";
  if (days === 1) return "昨天";
  if (days < 7) return `${days}天前`;
  if (days < 30) return `${Math.floor(days / 7)}周前`;
  if (days < 365) return `${Math.floor(days / 30)}个月前`;
  return `${Math.floor(days / 365)}年前`;
}

function formatFileSize(bytes) {
  if (!bytes) return "0 B";
  const units = ["B", "KB", "MB", "GB", "TB"];
  let n = bytes;
  let unitIndex = 0;
  while (n >= 1024 && unitIndex < units.length - 1) {
    n /= 1024;
    unitIndex += 1;
  }
  return `${n.toFixed(unitIndex === 0 ? 0 : 2)} ${units[unitIndex]}`;
}

function getInitial(name) {
  if (!name) return "S";
  return String(name).trim().charAt(0).toUpperCase() || "S";
}

function getFileIcon(ext) {
  const key = String(ext || "").toLowerCase();
  if (["png", "jpg", "jpeg", "gif", "bmp", "webp"].includes(key)) return "🖼";
  if (["pdf"].includes(key)) return "📄";
  if (["doc", "docx"].includes(key)) return "📝";
  if (["xls", "xlsx"].includes(key)) return "📊";
  if (["ppt", "pptx"].includes(key)) return "📽";
  if (["zip", "rar", "7z"].includes(key)) return "🗜";
  return "📁";
}

async function ensureTeacher() {
  await Auth.checkAuth();
  if (!Auth.state.user || Auth.state.user.role !== "teacher") {
    alert("权限不足，仅教师可访问");
    window.location.href = "dashboard.html";
    return false;
  }

  const usernameEl = document.getElementById("username");
  const avatarEl = document.getElementById("user-avatar");
  if (usernameEl) {
    usernameEl.textContent = Auth.state.user.name || Auth.state.user.email || "教师";
  }
  if (avatarEl) {
    avatarEl.textContent = getInitial(Auth.state.user.name || Auth.state.user.email || "T");
  }

  return true;
}

async function fetchStudents() {
  const container = document.getElementById("students-list");
  container.className = "loading";
  container.innerHTML = "加载中...";

  const data = await API.get("/api/users/students", { headers: getAuthHeaders() });
  allStudents = Array.isArray(data.students) ? data.students : [];
  renderStudents(allStudents);
}

function renderStudents(list) {
  const container = document.getElementById("students-list");
  if (!Array.isArray(list) || list.length === 0) {
    container.className = "empty-state";
    container.innerHTML = '<div class="empty-state-icon">👥</div><div>暂无学生数据</div>';
    return;
  }

  container.className = "students-grid";
  container.innerHTML = list
    .map(
      (student) => `
      <div class="student-card" data-student-id="${student.id}" role="button" tabindex="0">
        <div class="student-header">
          <div class="student-avatar">${escapeHtml(getInitial(student.name))}</div>
          <div class="student-info">
            <div class="student-name">${escapeHtml(student.name || "未命名")}</div>
            <div class="student-id">${escapeHtml(student.student_id || "未设置学号")}</div>
          </div>
        </div>
        <div class="student-details">
          <div>邮箱: ${escapeHtml(student.email || "-")}</div>
          <div>年级: ${escapeHtml(student.grade || "-")}</div>
          <div>班级: ${escapeHtml(student.class_name || "-")}</div>
        </div>
        <div class="student-stats">
          <span>${Number(student.document_count || 0)} 个文档</span>
          <span>${escapeHtml(formatDateAgo(student.created_at))}</span>
        </div>
      </div>
    `
    )
    .join("");
}

function bindStudentCardEvents() {
  const container = document.getElementById("students-list");
  if (!container) return;

  container.addEventListener("click", (event) => {
    const target = event.target;
    if (!(target instanceof Element)) return;
    const card = target.closest(".student-card[data-student-id]");
    if (!card) return;
    const studentId = Number(card.dataset.studentId);
    if (studentId) {
      openStudentDetail(studentId);
    }
  });

  container.addEventListener("keydown", (event) => {
    if (event.key !== "Enter" && event.key !== " ") return;
    const target = event.target;
    if (!(target instanceof Element)) return;
    const card = target.closest(".student-card[data-student-id]");
    if (!card) return;
    event.preventDefault();
    const studentId = Number(card.dataset.studentId);
    if (studentId) {
      openStudentDetail(studentId);
    }
  });
}

function bindSearch() {
  const input = document.getElementById("search-input");
  if (!input) return;

  input.addEventListener("input", (event) => {
    const keyword = String(event.target.value || "").trim().toLowerCase();
    if (!keyword) {
      renderStudents(allStudents);
      return;
    }

    const filtered = allStudents.filter((student) => {
      return [student.name, student.student_id, student.email, student.grade, student.class_name]
        .filter(Boolean)
        .some((field) => String(field).toLowerCase().includes(keyword));
    });
    renderStudents(filtered);
  });
}

async function openStudentDetail(studentId) {
  const requestSeq = ++state.detailRequestSeq;
  state.activeStudentId = studentId;
  showModal(true);
  setModalLoading();

  try {
    const [detail, docsResp] = await Promise.all([
      API.get(`/api/users/students/${studentId}`, { headers: getAuthHeaders() }),
      API.get(`/api/users/students/${studentId}/documents`, { headers: getAuthHeaders() }),
    ]);

    // Ignore stale response to avoid showing student/doc mismatch.
    if (requestSeq !== state.detailRequestSeq) {
      return;
    }

    const documents = Array.isArray(docsResp.documents) ? docsResp.documents : detail.documents || [];
    renderStudentDetail(detail.student, documents);
  } catch (error) {
    console.error("加载学生详情失败:", error);
    alert(`加载学生详情失败: ${error.message || error}`);
    showModal(false);
  }
}

function setModalLoading() {
  const nameEl = document.getElementById("modal-student-name");
  const docsEl = document.getElementById("documents-list");
  if (nameEl) nameEl.textContent = "加载中...";
  if (docsEl) docsEl.innerHTML = '<div class="loading">正在加载学生详情...</div>';
}

function renderStudentDetail(student, documents) {
  if (!student) return;
  state.activeStudentId = Number(student.id) || state.activeStudentId;

  const safeName = student.name || "未命名";
  document.getElementById("modal-avatar").textContent = getInitial(safeName);
  document.getElementById("modal-student-name").textContent = safeName;
  document.getElementById("modal-student-id").textContent = `学号: ${student.student_id || "未设置"}`;
  document.getElementById("modal-student-email").textContent = `邮箱: ${student.email || "-"}`;

  document.getElementById("detail-name").textContent = student.name || "-";
  document.getElementById("detail-student-id").textContent = student.student_id || "-";
  document.getElementById("detail-grade").textContent = student.grade || "-";
  document.getElementById("detail-class").textContent = student.class_name || "-";
  document.getElementById("detail-email").textContent = student.email || "-";
  document.getElementById("detail-created").textContent = formatDateTime(student.created_at);

  const count = Array.isArray(documents) ? documents.length : 0;
  document.getElementById("doc-count").textContent = String(count);

  const docsEl = document.getElementById("documents-list");
  if (!count) {
    docsEl.innerHTML = '<div class="empty-state"><div class="empty-state-icon">📭</div><div>该学生尚未上传文档</div></div>';
    return;
  }

  docsEl.innerHTML = documents
    .map(
      (doc) => `
      <div class="document-item">
        <div style="display:flex;align-items:center;flex:1;min-width:0;">
          <div class="document-icon">${getFileIcon(doc.file_type)}</div>
          <div class="document-info">
            <div class="document-name">${escapeHtml(doc.name || doc.original_name || "未命名文档")}</div>
            <div class="document-meta">${escapeHtml(doc.file_type || "-")} · ${escapeHtml(formatFileSize(doc.file_size))} · ${escapeHtml(formatDateTime(doc.created_at))}</div>
          </div>
        </div>
        <div style="display:flex;gap:8px;">
          <button class="button" data-action="view-doc" data-view-url="${escapeHtml(doc.view_url || "")}" data-student-id="${student.id}" data-doc-id="${doc.id}" style="padding:6px 12px;font-size:12px;">查看</button>
          <button class="button" data-action="download-doc" data-download-url="${escapeHtml(doc.download_url || "")}" data-student-id="${student.id}" data-doc-id="${doc.id}" style="padding:6px 12px;font-size:12px;">下载</button>
        </div>
      </div>
    `
    )
    .join("");
}

async function openTeacherDocByUrl(endpoint, mode) {
  if (!endpoint) return;
  const endpointPath = String(endpoint).startsWith("/") ? endpoint : `/${endpoint}`;

  // Open a blank tab synchronously to avoid popup blockers for async fetch.
  const previewWindow = mode === "view" ? window.open("about:blank", "_blank") : null;
  console.log("[doc-open] endpoint:", endpointPath, "mode:", mode);

  try {
    if (previewWindow && !previewWindow.closed) {
      previewWindow.document.open();
      previewWindow.document.write("<!doctype html><html><head><meta charset='utf-8'><title>文档加载中</title></head><body style='font-family:system-ui;padding:24px;color:#444;'>文档加载中...</body></html>");
      previewWindow.document.close();
    }

    const response = await fetch(`${API.baseURL}${endpointPath}`, {
      method: "GET",
      headers: getAuthHeaders(),
    });

    if (response.status === 401) {
      if (previewWindow && !previewWindow.closed) {
        previewWindow.close();
      }
      await Auth.refresh();
      return openTeacherDocByUrl(endpointPath, mode);
    }

    if (!response.ok) {
      throw new Error(`请求失败: ${response.status}`);
    }

    const blob = await response.blob();
    const url = window.URL.createObjectURL(blob);
    console.log("[doc-open] success:", { endpoint: endpointPath, type: blob.type, size: blob.size });

    if (mode === "download") {
      const link = document.createElement("a");
      link.href = url;
      link.download = "document";
      document.body.appendChild(link);
      link.click();
      document.body.removeChild(link);
      setTimeout(() => window.URL.revokeObjectURL(url), 3000);
      return;
    }

    if (previewWindow) {
      const escapedUrl = String(url).replace(/"/g, "&quot;");
      const mime = (blob.type || "application/octet-stream").replace(/"/g, "");
      previewWindow.document.open();
      previewWindow.document.write(
        `<!doctype html><html><head><meta charset="utf-8"><title>文档预览</title></head>` +
        `<body style="margin:0;background:#f5f7fa;">` +
        `<iframe src="${escapedUrl}" title="doc-preview" style="border:0;width:100vw;height:100vh;"></iframe>` +
        `<noscript><p style="padding:12px;">无法预览，请启用 JavaScript。文件类型: ${mime}</p></noscript>` +
        `</body></html>`
      );
      previewWindow.document.close();
      try {
        previewWindow.opener = null;
      } catch (_) {}
    } else {
      // Fallback: current tab preview if popup is blocked.
      window.location.href = url;
    }
    setTimeout(() => window.URL.revokeObjectURL(url), 5 * 60 * 1000);
  } catch (error) {
    if (previewWindow && !previewWindow.closed) {
      previewWindow.close();
    }
    console.error("查看/下载学生文档失败:", error);
    alert(`文档操作失败: ${error.message || error}`);
  }
}

function bindModalEvents() {
  const modal = document.getElementById("student-modal");
  if (!modal) return;

  modal.addEventListener("click", (event) => {
    if (event.target === modal) {
      showModal(false);
      return;
    }

    const btn = event.target.closest("button[data-action]");
    if (!btn) return;

    const action = btn.dataset.action;
    if (action === "view-doc") {
      const endpoint = btn.dataset.viewUrl || "";
      openTeacherDocByUrl(endpoint, "view");
    } else if (action === "download-doc") {
      const endpoint = btn.dataset.downloadUrl || "";
      openTeacherDocByUrl(endpoint, "download");
    }
  });
}

function showModal(show) {
  const modal = document.getElementById("student-modal");
  if (!modal) return;

  if (show) {
    modal.classList.add("active");
    modal.classList.add("is-open");
  } else {
    modal.classList.remove("active");
    modal.classList.remove("is-open");
    state.activeStudentId = null;
    state.detailRequestSeq += 1;
  }
}

window.closeModal = function closeModal() {
  showModal(false);
};

window.closeStudentModal = window.closeModal;

async function initStudentsPage() {
  try {
    const allowed = await ensureTeacher();
    if (!allowed) return;

    bindSearch();
    bindStudentCardEvents();
    bindModalEvents();
    await fetchStudents();
  } catch (error) {
    console.error("初始化学生管理页面失败:", error);
    alert("请先登录");
    window.location.href = "index.html";
  }
}

document.addEventListener("DOMContentLoaded", initStudentsPage);
