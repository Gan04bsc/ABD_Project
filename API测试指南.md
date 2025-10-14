# API 测试指南

## 测试环境准备

### 1. 启动后端服务
```bash
cd backend
python wsgi.py
```
服务将运行在 `http://localhost:5000`

### 2. 获取测试用户Token
```bash
# 学生登录（甘丰睿）
curl -X POST http://localhost:5000/api/auth/login \
  -H "Content-Type: application/json" \
  -d "{\"username\":\"student1\",\"password\":\"123456\"}"

# 老师登录（何东璟）
curl -X POST http://localhost:5000/api/auth/login \
  -H "Content-Type: application/json" \
  -d "{\"username\":\"teacher1\",\"password\":\"123456\"}"
```

保存返回的 `access_token`，后续请求需要使用。

---

## 测试场景

### 场景1: 学生创建预约

**请求**:
```bash
curl -X POST http://localhost:5000/api/schedule/book \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer <学生token>" \
  -d "{
    \"teacher_id\": 2,
    \"appointment_date\": \"2025-10-25\",
    \"time_slot\": \"14:00-15:00\",
    \"appointment_type\": \"学术咨询\",
    \"reason\": \"讨论毕业设计题目\"
  }"
```

**预期响应**:
```json
{
  "message": "预约创建成功",
  "appointment": {
    "id": 1,
    "status": "pending",
    ...
  }
}
```

---

### 场景2: 学生查看自己的预约

**请求**:
```bash
curl -X GET http://localhost:5000/api/schedule/appointments \
  -H "Authorization: Bearer <学生token>"
```

**预期响应**:
```json
{
  "appointments": [
    {
      "id": 1,
      "teacher": {
        "name": "何东璟",
        "department": "计算机学院"
      },
      "appointment_date": "2025-10-25",
      "time_slot": "14:00-15:00",
      "status": "pending"
    }
  ]
}
```

---

### 场景3: 老师查看待处理预约

**请求**:
```bash
curl -X GET "http://localhost:5000/api/schedule/appointments?status=pending" \
  -H "Authorization: Bearer <老师token>"
```

**预期响应**:
```json
{
  "appointments": [
    {
      "id": 1,
      "student": {
        "name": "甘丰睿"
      },
      "appointment_date": "2025-10-25",
      "time_slot": "14:00-15:00",
      "status": "pending"
    }
  ]
}
```

---

### 场景4: 老师接受预约

**请求**:
```bash
curl -X PATCH http://localhost:5000/api/schedule/appointments/1 \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer <老师token>" \
  -d "{\"status\": \"approved\"}"
```

**预期响应**:
```json
{
  "message": "预约状态更新成功",
  "appointment": {
    "id": 1,
    "status": "approved"
  }
}
```

---

### 场景5: 老师拒绝预约

**请求**:
```bash
curl -X PATCH http://localhost:5000/api/schedule/appointments/1 \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer <老师token>" \
  -d "{\"status\": \"rejected\"}"
```

**预期响应**:
```json
{
  "message": "预约状态更新成功",
  "appointment": {
    "id": 1,
    "status": "rejected"
  }
}
```

---

### 场景6: 学生取消预约

**请求**:
```bash
curl -X PATCH http://localhost:5000/api/schedule/appointments/1 \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer <学生token>" \
  -d "{\"status\": \"cancelled\"}"
```

**预期响应**:
```json
{
  "message": "预约状态更新成功",
  "appointment": {
    "id": 1,
    "status": "cancelled"
  }
}
```

---

### 场景7: 查询已预约时间段

**请求**:
```bash
curl -X GET "http://localhost:5000/api/schedule/booked-slots/2?date=2025-10-25"
```

**预期响应**:
```json
{
  "teacher_id": 2,
  "date": "2025-10-25",
  "booked_slots": [
    "14:00-15:00",
    "15:00-16:00"
  ]
}
```

---

### 场景8: 时间冲突检测

**步骤1** - 创建第一个预约:
```bash
curl -X POST http://localhost:5000/api/schedule/book \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer <学生token>" \
  -d "{
    \"teacher_id\": 2,
    \"appointment_date\": \"2025-10-26\",
    \"time_slot\": \"10:00-11:00\",
    \"appointment_type\": \"课程辅导\",
    \"reason\": \"复习考试内容\"
  }"
```

**步骤2** - 尝试创建相同时间段的预约:
```bash
curl -X POST http://localhost:5000/api/schedule/book \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer <学生token>" \
  -d "{
    \"teacher_id\": 2,
    \"appointment_date\": \"2025-10-26\",
    \"time_slot\": \"10:00-11:00\",
    \"appointment_type\": \"学术咨询\",
    \"reason\": \"讨论论文\"
  }"
```

**预期响应** (第二个请求应该失败):
```json
{
  "error": "该时间段已被预约"
}
```
HTTP状态码: 409

---

## 错误场景测试

### 测试1: 无权限操作

**学生尝试接受预约**:
```bash
curl -X PATCH http://localhost:5000/api/schedule/appointments/1 \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer <学生token>" \
  -d "{\"status\": \"approved\"}"
```

**预期响应**:
```json
{
  "error": "无权操作该预约"
}
```
HTTP状态码: 403

---

### 测试2: 预约过去的日期

**请求**:
```bash
curl -X POST http://localhost:5000/api/schedule/book \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer <学生token>" \
  -d "{
    \"teacher_id\": 2,
    \"appointment_date\": \"2020-01-01\",
    \"time_slot\": \"14:00-15:00\",
    \"appointment_type\": \"学术咨询\",
    \"reason\": \"测试\"
  }"
```

**预期响应**:
```json
{
  "error": "预约日期不能是过去的日期"
}
```
HTTP状态码: 400

---

### 测试3: 无效的预约类型

**请求**:
```bash
curl -X POST http://localhost:5000/api/schedule/book \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer <学生token>" \
  -d "{
    \"teacher_id\": 2,
    \"appointment_date\": \"2025-10-25\",
    \"time_slot\": \"14:00-15:00\",
    \"appointment_type\": \"无效类型\",
    \"reason\": \"测试\"
  }"
```

**预期响应**:
```json
{
  "error": "预约类型必须是: 学术咨询, 课程辅导, 项目讨论, 其他"
}
```
HTTP状态码: 400

---

## 使用 Postman 测试

### 1. 导入环境变量

创建环境变量:
- `base_url`: `http://localhost:5000`
- `student_token`: (登录后获取)
- `teacher_token`: (登录后获取)

### 2. 创建请求集合

**Collection**: 预约系统API

**文件夹1: 认证**
- POST {{base_url}}/api/auth/login (学生登录)
- POST {{base_url}}/api/auth/login (老师登录)

**文件夹2: 学生功能**
- POST {{base_url}}/api/schedule/book
  - Headers: `Authorization: Bearer {{student_token}}`
- GET {{base_url}}/api/schedule/appointments
  - Headers: `Authorization: Bearer {{student_token}}`
- PATCH {{base_url}}/api/schedule/appointments/:id
  - Headers: `Authorization: Bearer {{student_token}}`
  - Body: `{"status": "cancelled"}`

**文件夹3: 老师功能**
- GET {{base_url}}/api/schedule/appointments?status=pending
  - Headers: `Authorization: Bearer {{teacher_token}}`
- PATCH {{base_url}}/api/schedule/appointments/:id
  - Headers: `Authorization: Bearer {{teacher_token}}`
  - Body: `{"status": "approved"}`

**文件夹4: 公共功能**
- GET {{base_url}}/api/schedule/booked-slots/:teacher_id?date=2025-10-25

---

## Python 测试脚本

可以使用 `requests` 库编写自动化测试：

```python
import requests
from datetime import date, timedelta

BASE_URL = "http://localhost:5000"

# 1. 学生登录
response = requests.post(f"{BASE_URL}/api/auth/login", json={
    "username": "student1",
    "password": "123456"
})
student_token = response.json()["access_token"]

# 2. 老师登录
response = requests.post(f"{BASE_URL}/api/auth/login", json={
    "username": "teacher1",
    "password": "123456"
})
teacher_token = response.json()["access_token"]

# 3. 学生创建预约
tomorrow = (date.today() + timedelta(days=1)).isoformat()
response = requests.post(
    f"{BASE_URL}/api/schedule/book",
    json={
        "teacher_id": 2,
        "appointment_date": tomorrow,
        "time_slot": "14:00-15:00",
        "appointment_type": "学术咨询",
        "reason": "讨论毕业设计"
    },
    headers={"Authorization": f"Bearer {student_token}"}
)
print("创建预约:", response.json())

# 4. 老师查看预约
response = requests.get(
    f"{BASE_URL}/api/schedule/appointments?status=pending",
    headers={"Authorization": f"Bearer {teacher_token}"}
)
print("待处理预约:", response.json())

# 5. 老师接受预约
appointment_id = response.json()["appointments"][0]["id"]
response = requests.patch(
    f"{BASE_URL}/api/schedule/appointments/{appointment_id}",
    json={"status": "approved"},
    headers={"Authorization": f"Bearer {teacher_token}"}
)
print("接受预约:", response.json())
```

---

## 测试检查清单

- [ ] 学生可以成功创建预约
- [ ] 学生可以查看自己的预约列表
- [ ] 学生可以取消自己的预约
- [ ] 学生不能操作他人的预约
- [ ] 学生不能接受/拒绝预约
- [ ] 老师可以查看与自己相关的预约
- [ ] 老师可以接受预约
- [ ] 老师可以拒绝预约
- [ ] 老师可以标记预约为已完成
- [ ] 系统正确检测时间冲突
- [ ] 不能预约过去的日期
- [ ] 预约类型验证正确
- [ ] 查询已预约时间段功能正常
- [ ] 状态筛选功能正常

---

**提示**: 建议按照上述场景顺序进行测试，确保每个功能都能正常工作。

