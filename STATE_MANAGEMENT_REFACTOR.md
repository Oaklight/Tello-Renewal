# 状态管理系统重构总结

## 概述

我们成功地将 Tello renewal 系统的状态管理从单文件缓存重构为基于目录的状态管理系统，提供了更好的组织结构和功能分离。

## 主要变更

### 1. 配置更新

**之前:**

```toml
[renewal]
cache_file_path = "DUE_DATE"
exec_status_file_path = "EXEC_STATUS"
```

**现在:**

```toml
[renewal]
state_folder_path = ".tello_state"  # 统一的状态目录
```

### 2. 文件结构

新的状态管理系统在指定目录下创建以下文件：

```
.tello_state/
├── due_date      # 存储下次renewal的到期日期
└── run_state     # 存储最近一次运行的状态信息
```

### 3. 核心功能

#### DueDateCache (重构)

- **文件**: `state_folder/due_date`
- **格式**: 纯文本，ISO 日期格式 (YYYY-MM-DD)
- **功能**: 存储和管理 renewal 到期日期
- **更新时机**: 每次从网站获取到 renewal 日期时，如果与缓存不一致则更新

#### RunStateCache (新增)

- **文件**: `state_folder/run_state`
- **格式**: JSON
- **内容**:
  ```json
  {
    "date": "2025-11-22T09:37:54.635066", // 执行时间 (芝加哥时区)
    "success": true, // 是否成功
    "dry": true // 是否为dry run
  }
  ```

### 4. 智能跳过逻辑

新系统实现了更智能的 renewal 跳过逻辑：

1. **日期范围检查**: 如果当前日期不在 renewal 窗口内，跳过
2. **成功状态检查**: 如果今天已经成功执行过非 dry-run 的 renewal，跳过
3. **Dry run 处理**: 如果之前只是 dry run 成功，允许执行真实的 renewal

### 5. 时区支持

- 添加了芝加哥时区支持 (`America/Chicago`)
- 所有时间比较都基于芝加哥时间
- 新增依赖: `pytz>=2023.3`

## 向后兼容性

- 保留了原有的`ExecutionStatusCache`类以确保向后兼容
- 新旧系统并行运行，逐步迁移
- 配置文件自动支持新的`state_folder_path`参数

## 测试结果

根据 Docker 测试结果：

- ✅ `run_state`文件成功创建并包含正确的 JSON 格式数据
- ✅ 芝加哥时区时间戳正确记录
- ✅ Dry run 状态正确标记
- ✅ 新的状态管理逻辑正常工作

## 使用示例

### 配置文件

```toml
[renewal]
state_folder_path = "/app/logs/state"  # 可以是绝对路径或相对路径
days_before_renewal = 1
```

### 状态文件示例

**due_date 文件:**

```
2025-12-14
```

**run_state 文件:**

```json
{
  "date": "2025-11-22T09:37:54.635066",
  "success": true,
  "dry": true
}
```

## 优势

1. **更好的组织**: 所有状态文件集中在一个目录下
2. **功能分离**: due_date 和 run_state 分别管理不同的状态信息
3. **时区感知**: 基于芝加哥时间的准确时间管理
4. **智能跳过**: 避免重复执行已成功的 renewal
5. **灵活配置**: 支持自定义状态目录路径
6. **向后兼容**: 不破坏现有功能

## 下一步

建议在后续版本中：

1. 逐步移除旧的`ExecutionStatusCache`系统
2. 添加状态文件的清理和维护功能
3. 考虑添加状态历史记录功能
