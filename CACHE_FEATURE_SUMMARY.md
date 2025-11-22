# DUE_DATE 缓存功能实现总结

## 问题描述

原程序每天运行一次，频率过高，容易触发上游机器人检测。

## 解决方案

实现了基于本地缓存文件的日期检查机制，避免频繁运行程序。

## 实现的功能

### 1. DUE_DATE 缓存文件机制

- 创建了 `DueDateCache` 类来管理缓存文件
- 支持读取、写入、清除缓存文件
- 自动验证缓存文件格式和有效性
- 提供日期范围检查功能

### 2. 配置参数

- 复用现有的 `days_before_renewal` 参数作为缓存日期检查的范围
- 添加了 `cache_file_path` 参数用于指定缓存文件路径

### 3. CLI 命令增强

- 添加了 `--force` / `-f` 参数：强制忽略缓存的到期日期进行续费检查
- 该参数完全尊重 `--dry-run` 标志

### 4. 智能续费逻辑

- 每次运行时首先检查缓存文件
- 如果当前日期在缓存日期的 `days_before_renewal` 范围内，则跳过续费检查
- 使用 `--force` 参数可以绕过缓存检查
- 在非 dry-run 模式下，会将实际的续费日期写入缓存

### 5. 状态管理

- 使用 `RenewalStatus.SKIPPED` 状态表示跳过的续费检查
- 为跳过的续费检查设置了专门的退出码（7）

## 工作流程

1. **正常运行**：程序检查缓存文件，如果在指定范围内则跳过续费检查
2. **强制运行**：使用 `--force` 参数可以忽略缓存，强制进行续费检查
3. **缓存更新**：在实际续费检查后，将真实的续费日期写入缓存文件
4. **Dry-run 模式**：在 dry-run 模式下不会更新缓存文件

## 使用示例

```bash
# 正常运行（会检查缓存）
tello-renewal renew

# 强制运行（忽略缓存）
tello-renewal renew --force

# 强制运行但不实际操作（dry-run + force）
tello-renewal renew --force --dry-run

# 查看状态（会更新DUE_DATE缓存）
tello-renewal status

# 查看帮助
tello-renewal renew --help
```

## 配置示例

```toml
[renewal]
auto_renew = true
days_before_renewal = 23  # 既控制续费触发时机，也作为缓存检查范围
max_retries = 3
retry_delay = 300
dry_run = false
cache_file_path = "./DUE_DATE"  # DUE_DATE缓存文件路径
exec_status_file_path = "./EXEC_STATUS"  # 执行状态缓存文件路径
```

## 退出码

- `0`: 续费成功
- `5`: 续费失败
- `6`: 续费未到期
- `7`: 跳过续费检查（缓存命中）
- `1`: 一般错误

## 缓存文件格式

### DUE_DATE 文件

```
2025-12-14
```

### EXEC_STATUS 文件

```
2025-11-22T22:05:51.504815
success
```

## 日志示例

当缓存功能工作时，会看到类似以下的日志：

### DUE_DATE 缓存日志

```
2025-11-22 21:59:41.865 | INFO | tello_renewal.utils.cache:write_cached_date:80 - Cached renewal date: 2025-12-14
2025-11-22 21:59:41.865 | INFO | tello_renewal.utils.cache:is_within_range:105 - Date check: current=2025-11-22, cached=2025-12-14, diff=22 days, range=23 days, within_range=True
```

### 执行状态缓存日志

```
2025-11-22 22:05:51.504 | INFO | tello_renewal.utils.cache:write_execution_status:284 - Cached execution status: 2025-11-22 22:05:51.504815 - success
2025-11-22 22:05:51.504 | INFO | tello_renewal.utils.cache:should_retry_renewal:313 - In renewal window: 22 days until renewal
2025-11-22 22:05:51.504 | INFO | tello_renewal.utils.cache:should_retry_renewal:332 - Renewal was successful today, skipping retry
```

## 故障排除

### 问题：缓存文件没有创建

**原因**：缓存目录不存在
**解决**：确保 `cache_file_path` 指向的目录存在，或使用相对路径如 `./DUE_DATE`

### 问题：缓存功能不工作

**原因**：使用的是旧版本代码
**解决**：确保使用最新版本的代码，包含缓存功能

## 测试验证

缓存功能已通过以下测试：

- ✅ 缓存文件读写功能
- ✅ 日期范围检查逻辑
- ✅ --force 参数绕过缓存
- ✅ dry-run 模式不更新缓存
- ✅ 配置文件正确加载
- ✅ 退出码正确设置

## 效果

通过这个实现，程序现在可以：

1. 避免频繁运行导致的上游机器人检测
2. 保持灵活性，支持强制运行
3. 维持原有的所有功能
4. 提供清晰的日志和状态反馈
