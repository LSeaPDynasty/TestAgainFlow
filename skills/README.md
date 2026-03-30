# Skills - Claude Code 技能集

本目录包含 TestFlow 项目的 Claude Code 自定义技能。

## 📁 可用技能

### 🔍 code-review.md
**代码审查技能** - 严格审查代码质量、安全性和最佳实践

**功能**:
- 安全性检查（硬编码密钥、注入漏洞）
- 代码质量评估（异常处理、复杂度）
- 性能分析（数据库查询、缓存）
- 可维护性审查（结构、耦合度）
- 最佳实践验证
- Python/TypeScript 特定检查

**使用方法**:
```bash
# 审查单个文件
/review backend/app/main.py

# 审查整个目录
/review backend/

# 按维度审查
/review --security backend/app/
/review --performance executor/

# 生成详细报告
/review --detailed frontend/src/
```

**输出**: 包含 P0/P1/P2 分级的详细审查报告

---

## 🚀 如何使用

### 前置条件
1. 安装 [Claude Code](https://claude.com/claude-code)
2. 克隆本项目到本地
3. 在项目根目录启动 Claude Code

### 使用技能

Claude Code 会自动识别项目中的 skills，你可以：

1. **直接调用**:
   ```
   @claude /review backend/app/models/
   ```

2. **在对话中使用**:
   ```
   请使用 /review 技能审查后端代码
   ```

3. **结合其他命令**:
   ```
   /review backend/app/ && /fix --all
   ```

---

## 📝 创建自定义技能

### 技能文件结构

```markdown
# 技能名称

简短描述技能的功能

## 使用场景
- 场景1
- 场景2

## 执行步骤
1. 步骤1
2. 步骤2

## 输出格式
描述输出格式

## 示例
\`\`\`bash
示例命令
\`\`\`
```

### 技能最佳实践

1. **命名规范**: 使用小写字母和连字符，如 `code-review.md`
2. **清晰描述**: 开头明确说明技能用途
3. **结构化内容**: 使用清晰的章节划分
4. **具体示例**: 提供使用示例和输出格式
5. **注意事项**: 说明使用限制和注意事项

---

## 🔧 技能开发计划

### 待开发技能

- [ ] **test-generator** - 自动生成单元测试
- [ ] **api-docs** - 生成API文档
- [ ] **refactor** - 代码重构建议
- [ ] **security-scan** - 安全漏洞扫描
- [ ] **performance-profiler** - 性能分析
- [ ] **dependency-check** - 依赖检查

---

## 🤝 贡献指南

欢迎贡献新的技能！

### 提交新技能

1. 在 `skills/` 目录创建新的 `.md` 文件
2. 按照上述结构编写技能文档
3. 添加使用示例和输出格式
4. 提交 Pull Request

### 技能审核标准

- ✅ 功能明确，有实际使用价值
- ✅ 文档完整，包含示例
- ✅ 输出格式清晰
- ✅ 经过测试验证

---

## 📖 相关资源

- [Claude Code 官方文档](https://claude.com/claude-code/docs)
- [项目主 README](../README.md)
- [开发指南](../docs/)

---

## 📄 许可证

本技能集遵循项目的 MIT License。

---

<div align="center">

**让 Claude Code 更智能地工作！**

Made with ❤️ by TestFlow Team

</div>
