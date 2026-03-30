# TestFlow 前端权限管理功能

## 功能概述

前端已实现完整的权限管理UI，支持：

1. **用户角色显示** - 在Header显示用户角色（超级管理员、管理员、普通成员）
2. **菜单权限控制** - 根据用户角色动态显示菜单项
3. **项目成员管理** - 可视化管理项目成员和角色
4. **审计日志查看** - 查询和查看操作审计日志

## 新增页面

### 1. 项目成员管理页面 (`/projects/:projectId/members`)

**功能**：
- 查看项目所有成员
- 添加新成员（通过用户名）
- 修改成员角色（查看者、编辑者、管理员）
- 移除项目成员
- 显示成员加入时间

**角色说明**：
- **查看者** - 只能查看项目内容
- **编辑者** - 可以创建和编辑资源
- **管理员** - 可以管理项目成员
- **所有者** - 项目的最高权限者（不可修改）

### 2. 审计日志页面 (`/audit-logs`)

**功能**：
- 查看所有操作审计日志
- 按操作类型、资源类型、项目ID筛选
- 查看操作详情（包括详细信息JSON）
- 显示操作时间、用户、IP地址等

**操作类型**：
- 用户操作：登录、登出、注册
- 项目操作：创建、更新、删除项目
- 资源操作：元素、步骤、流程、测试用例的增删改
- 执行操作：执行测试用例
- 权限操作：添加/移除成员、修改角色

## 权限控制

### 菜单权限

- **所有用户**：基础功能、审计日志
- **管理员及以上**：用户管理

### 功能权限

1. **项目访问**
   - 只能访问自己是成员的项目
   - 项目列表自动过滤无权限项目

2. **操作权限**
   - 创建/编辑/删除：需要相应权限
   - 成员管理：需要项目管理员权限
   - 系统管理：需要系统管理员权限

## 用户界面变化

### Header组件

- 显示用户名和角色标签
- 添加"审计日志"菜单项
- "用户管理"仅管理员可见

### Sidebar组件

- 添加"审计日志"菜单项
- "用户管理"仅管理员可见
- 根据用户权限动态显示菜单

### 项目页面

- 操作列添加"成员"按钮
- 点击跳转到项目成员管理页面

## API调用

所有权限相关API都通过 `/api/v1/permissions/` 路径：

```typescript
// 获取项目成员
GET /permissions/projects/:projectId/members

// 添加项目成员
POST /permissions/projects/:projectId/members

// 更新成员角色
PUT /permissions/projects/:projectId/members/:userId

// 移除项目成员
DELETE /permissions/projects/:projectId/members/:userId

// 获取审计日志
GET /permissions/audit-logs

// 获取可访问项目列表
GET /permissions/my-projects
```

## 使用流程

### 1. 创建超级管理员

```bash
cd backend
python init_admin.py
```

### 2. 登录系统

使用创建的超级管理员账户登录。

### 3. 创建项目并邀请成员

1. 创建新项目（创建者自动成为项目所有者）
2. 进入项目详情，点击"成员"按钮
3. 添加成员并分配角色

### 4. 查看审计日志

1. 点击Header用户菜单中的"审计日志"
2. 使用筛选条件查找特定操作
3. 点击"详情"查看完整操作信息

## 权限验证

所有API请求都会：
1. 自动携带JWT Token（通过axios interceptor）
2. 后端验证用户身份和权限
3. 权限不足时显示错误提示
4. Token过期时自动跳转登录页

## 开发说明

### 添加权限检查

```typescript
import { getStoredUser, isAdmin } from '@/services/auth';

const user = getStoredUser();
if (isAdmin(user)) {
  // 管理员功能
}
```

### 调用权限API

```typescript
import { getProjectMembers, addProjectMember } from '@/services/permissions';

// 获取成员
const members = await getProjectMembers(projectId);

// 添加成员
await addProjectMember(projectId, { username: 'user1', role: 'editor' });
```

## 注意事项

1. **Token管理**
   - Token存储在localStorage中
   - 每次API请求自动携带
   - 过期时需要重新登录

2. **权限缓存**
   - 用户信息缓存1分钟
   - 权限变更后需要刷新页面

3. **项目过滤**
   - 项目列表自动过滤无权限项目
   - 前端显示可能与后端实际数据不同

4. **成员管理**
   - 不能移除项目所有者
   - 不能修改自己的角色（防止权限丢失）

## 后续优化

- [ ] 添加项目成员批量操作
- [ ] 实现实时权限更新（WebSocket）
- [ ] 添加权限申请审批流程
- [ ] 优化审计日志搜索和导出功能
- [ ] 添加操作统计图表
