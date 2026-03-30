# TestFlow 权限管理系统使用说明

## 概述

TestFlow 现已实现完整的权限管理和操作审计功能，支持：

- **三级用户角色**：普通成员、管理员、超级管理员
- **项目级权限控制**：项目成员只能访问有权限的项目
- **细粒度权限**：查看者、编辑者、项目管理员、项目所有者
- **操作审计日志**：记录所有敏感操作

## 用户角色

### 1. 超级管理员 (super_admin)
- 系统最高权限
- 可以访问所有项目和功能
- 可以管理用户角色
- 可以查看所有审计日志

### 2. 管理员 (admin)
- 可以管理项目成员
- 可以查看系统级别的审计日志
- 不能修改用户角色

### 3. 普通成员 (member)
- 只能访问被授权的项目
- 只能查看自己相关的审计日志

## 项目权限级别

### 1. 查看者 (viewer)
- 只能查看项目内容
- 不能进行任何修改操作

### 2. 编辑者 (editor)
- 可以创建和编辑资源（元素、步骤、流程、测试用例）
- 不能删除项目或管理成员

### 3. 项目管理员 (admin)
- 可以编辑项目配置
- 可以添加/移除项目成员
- 可以修改成员角色
- 不能删除项目

### 4. 项目所有者 (owner)
- 项目的最高权限
- 可以删除项目
- 可以执行所有项目操作
- 每个项目必须有且仅有一个所有者

## 初始化部署

### 1. 运行数据库迁移

```bash
cd backend
alembic upgrade head
```

### 2. 创建超级管理员

```bash
python init_admin.py
```

按提示输入：
- 超级管理员用户名（默认: admin）
- 邮箱（可选）
- 密码

### 3. 登录系统

使用创建的超级管理员账户登录系统：
```bash
POST /api/v1/users/login
{
  "username": "admin",
  "password": "your_password"
}
```

## API使用指南

### 1. 获取我的可访问项目

```bash
GET /api/v1/permissions/my-projects
Authorization: Bearer <your_token>
```

### 2. 查看项目成员

```bash
GET /api/v1/permissions/projects/{project_id}/members
Authorization: Bearer <your_token>
```

### 3. 添加项目成员

```bash
POST /api/v1/permissions/projects/{project_id}/members
Authorization: Bearer <your_token>
Content-Type: application/json

{
  "username": "member_username",
  "role": "editor"
}
```

### 4. 修改成员角色

```bash
PUT /api/v1/permissions/projects/{project_id}/members/{user_id}
Authorization: Bearer <your_token>
Content-Type: application/json

{
  "role": "admin"
}
```

### 5. 移除项目成员

```bash
DELETE /api/v1/permissions/projects/{project_id}/members/{user_id}
Authorization: Bearer <your_token>
```

### 6. 查看审计日志

```bash
GET /api/v1/permissions/audit-logs?page=1&page_size=20&project_id=1
Authorization: Bearer <your_token>
```

查询参数：
- `page`: 页码
- `page_size`: 每页数量
- `project_id`: 项目ID（可选）
- `resource_type`: 资源类型（可选）
- `resource_id`: 资源ID（可选）
- `action`: 操作类型（可选）

## 权限检查规则

### 项目访问规则
1. 超级管理员可以访问所有项目
2. 普通用户只能访问自己是成员的项目
3. 访问任何项目资源前都会检查权限

### 操作权限规则
- **创建项目**: 创建者自动成为项目所有者
- **编辑项目**: 需要编辑者及以上权限
- **删除项目**: 仅项目所有者
- **管理成员**: 需要项目管理员及以上权限
- **查看成员**: 需要是项目成员

## 审计日志记录

系统会自动记录以下操作：

### 用户操作
- 登录/登出
- 注册

### 项目操作
- 创建/更新/删除项目
- 查看项目详情

### 资源操作
- 创建/更新/删除元素
- 创建/更新/删除步骤
- 创建/更新/删除流程
- 创建/更新/删除测试用例
- 执行测试用例

### 权限操作
- 添加项目成员
- 移除项目成员
- 修改成员角色

### 日志内容
每条审计日志包含：
- 操作用户ID和用户名
- 操作类型
- 资源类型和ID
- 项目ID
- 操作详情（JSON格式）
- IP地址
- 用户代理
- 操作时间
- 操作结果（成功/失败）

## 安全建议

1. **定期更换密码**: 建议超级管理员定期更换密码
2. **最小权限原则**: 只授予用户必要的权限
3. **定期审计日志**: 定期检查审计日志，发现异常操作
4. **备份重要数据**: 定期备份项目和审计日志数据
5. **网络安全**: 在生产环境使用HTTPS协议

## 常见问题

### Q: 如何恢复被误删的项目成员？
A: 项目管理员可以通过"添加项目成员"功能重新添加成员。

### Q: 如何修改项目所有者？
A: 目前不支持直接转移所有权。建议创建新项目或将现有项目所有者提升为管理员，然后创建新的所有者账户。

### Q: 审计日志会占用大量空间吗？
A: 审计日志采用JSON格式存储，通常不会占用大量空间。如有需要，可以定期清理旧的审计日志。

### Q: 普通用户可以查看审计日志吗？
A: 普通用户只能查看自己有权限的项目的审计日志，无法查看系统级别的所有日志。

## 技术实现

权限系统基于以下技术：
- **数据库**: SQLite/MySQL/PostgreSQL
- **ORM**: SQLAlchemy
- **认证**: JWT Token
- **权限模型**: RBAC (基于角色的访问控制)
- **审计日志**: 异步日志记录

## 更新日志

### v1.0.0 (2026-03-30)
- 实现三级用户角色系统
- 实现项目级权限控制
- 实现操作审计日志
- 添加项目成员管理功能
- 创建超级管理员初始化工具
