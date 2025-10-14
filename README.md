# Study Abroad 项目骨架

这是根据提供的框架生成的最小可运行骨架（后端 Flask + 前端静态页面）。

## 准备环境（Windows PowerShell）

```powershell
# 进入项目目录
cd d:\ADB_Project

# 创建并激活虚拟环境（可选）
python -m venv .venv
.\.venv\Scripts\Activate.ps1

# 安装后端依赖
pip install -r backend\requirements.txt

# 复制环境变量模板
Copy-Item backend\.env.example backend\.env -Force

# 初始化数据库（第一次）
$env:FLASK_APP = "backend/wsgi.py"
$env:FLASK_ENV = "development"
flask db init
flask db migrate -m "init"
flask db upgrade

# 启动后端（含 SocketIO）
python backend\wsgi.py
```

后端启动后，浏览器访问 http://localhost:5000/health 可以看到健康检查。

## 前端
直接打开 `frontend/index.html` 即可（或用任意静态服务器）。页面按钮会调用后端接口示例。

## 目录说明
- backend/app: Flask 应用工厂、扩展、模型、蓝图、服务、任务、测试
- backend/migrations: Alembic 迁移目录
- frontend: 静态页面与脚本

## 下一步建议
- 实现真实的用户注册/登录（JWT）与权限控制
- 完善文档上传、聊天（SocketIO）、日程预约、推荐信流程
- 接入存储（S3/本地）、邮件服务、SSO、GPA 计算等
- 为蓝图与服务添加单元测试

## 认证 API（快速参考）
- POST /api/auth/register { email, password, name? } -> 201
- POST /api/auth/login { email, password } -> 200 { access_token, refresh_token }
- POST /api/auth/refresh (Authorization: Bearer <refresh>) -> 200 { access_token }
- GET /api/users/me (Authorization: Bearer <access>) -> 200 身份信息
