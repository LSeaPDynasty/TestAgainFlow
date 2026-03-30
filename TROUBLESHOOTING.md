# 前端问题修复指南

## 问题：登录admin但显示lsea用户

### 🔍 问题原因
1. **localStorage缓存混乱**：浏览器缓存了旧的登录信息
2. **API响应数据结构**：Header组件使用了错误的缓存数据

### ✅ 解决方案

#### 方法1：清除浏览器缓存（推荐）

1. **打开浏览器开发者工具**
   - Chrome/Edge: 按 F12
   - Firefox: 按 Ctrl+Shift+I

2. **清除Local Storage**
   - 开发者工具 → Application → Local Storage
   - 找到 `http://localhost:3000` (或相应域名)
   - 右键 → Clear

3. **刷新页面**
   - 按 Ctrl+Shift+R 强制刷新
   - 重新登录 admin/admin123

#### 方法2：使用控制台清除缓存

在浏览器控制台（Console）中执行：

```javascript
localStorage.clear();
location.reload();
```

#### 方法3：无痕模式测试

- Chrome/Edge: Ctrl+Shift+N
- Firefox: Ctrl+Shift+P
- 访问 http://localhost:3000
- 登录 admin/admin123

## 问题：审计日志无法查看

### 🔍 问题原因
审计日志需要管理员权限，普通用户无法查看。

### ✅ 解决方案

**使用管理员账户登录**：
- 用户名：`admin`
- 密码：`admin123`
- 角色：超级管理员

或者提升当前用户的权限（需要修改数据库）。

## 问题：项目选择器无法选择

### 🔍 问题原因
1. 数据结构路径错误
2. 项目列表为空或加载失败

### ✅ 解决方案

**检查项目数据**：

1. **打开浏览器控制台**（F12）
2. **切换到 Network 标签**
3. **刷新页面，查看 `/api/v1/projects` 请求**
4. **检查响应数据**：
   ```json
   {
     "code": 0,
     "data": {
       "items": [...],
       "total": 2
     }
   }
   ```

**如果项目列表为空**：
- 确保已登录
- 确保用户是项目成员
- 联系项目管理员添加权限

**如果无法选择项目**：
- 点击项目选择器
- 查看是否有项目列表
- 检查控制台是否有错误

## 🚨 完整重置步骤

如果上述方法都无法解决问题，执行完整重置：

### 1. 停止所有服务
```bash
# 停止后端 (Ctrl+C)
# 停止前端 (Ctrl+C)
```

### 2. 清除浏览器数据
```
开发者工具 → Application → Clear site data
```

### 3. 重新启动服务
```bash
# 后端
cd backend
python -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

# 前端
cd frontend
npm run dev
```

### 4. 重新登录
- 访问 http://localhost:3000
- 用户名：admin
- 密码：admin123

### 5. 验证功能
- ✅ 检查Header显示的用户名是否为 admin
- ✅ 检查是否有红色"超级管理员"标签
- ✅ 尝试选择项目
- ✅ 访问审计日志页面

## 🔧 调试技巧

### 查看当前用户信息

在浏览器控制台执行：

```javascript
// 查看存储的token
localStorage.getItem('testflow_access_token')

// 查看存储的用户信息
JSON.parse(localStorage.getItem('testflow_user'))

// 查看所有localStorage
console.log(localStorage)
```

### 查看API请求

1. 打开开发者工具 → Network
2. 刷新页面
3. 查看 `/api/v1/users/me` 请求
4. 检查响应中的用户信息

### 手动刷新用户信息

```javascript
// 在控制台执行
location.reload();
```

## 📝 已修复的代码问题

### 1. Header组件用户显示
- ❌ 之前：使用缓存的旧用户数据
- ✅ 现在：使用API返回的实际用户数据

### 2. 项目选择器数据结构
- ❌ 之前：错误的数据路径 `projectsData?.items`
- ✅ 现在：正确的数据路径 `projectsData?.data?.data?.items`

### 3. 审计日志错误处理
- ❌ 之前：权限错误导致白屏
- ✅ 现在：显示友好的错误提示

### 4. 登录缓存清理
- ❌ 之前：保留旧的认证缓存
- ✅ 现在：登录时自动清除所有缓存

## 🎯 验证修复效果

修复后应该看到：

1. ✅ 登录admin后显示admin用户名
2. ✅ 显示红色"超级管理员"标签
3. ✅ 项目选择器显示可用项目
4. ✅ 可以选择项目
5. ✅ 审计日志页面正常显示
6. ✅ 可以查看操作日志

## 🆘 仍然有问题？

如果上述步骤都尝试过仍有问题：

1. **检查后端日志**
   ```bash
   # 后端控制台应该显示请求日志
   # 检查是否有错误信息
   ```

2. **检查数据库**
   ```bash
   cd backend
   python check_db.py
   # 查看用户和项目数据
   ```

3. **重新初始化管理员**
   ```bash
   cd backend
   python init_admin.py
   # 创建新的管理员账户
   ```

4. **联系支持**
   - 提供浏览器控制台错误信息
   - 提供后端日志
   - 提供Network请求详情
