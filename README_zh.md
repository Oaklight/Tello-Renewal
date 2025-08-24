# Tello-Renewal

[English Version](README_en.md) | [中文版](README_zh.md)

使用网页自动化技术的 Tello 手机套餐自动续费系统。

## 功能特性

- 🔄 使用 Selenium 网页自动化进行自动套餐续费
- 📧 成功/失败邮件通知
- 🧪 测试模式（干运行）
- ⚙️ TOML 配置文件及验证
- 🔒 安全的凭据处理
- 📊 全面的日志记录
- 🐳 Docker 支持，包含可重用基础镜像

## 安装

### 从源码安装

```bash
# 克隆仓库
git clone <repository-url>
cd tello-renewal

# 以开发模式安装
pip install -e .

# 或从PyPI安装（发布后）
pip install tello-renewal
```

### 系统要求

- Python 3.10+
- Firefox、Chrome 或 Edge 浏览器
- 对应浏览器的 WebDriver（Firefox 需要 geckodriver）

## 快速开始

1. **创建配置文件：**

   ```bash
   tello-renewal config-init
   ```

2. **编辑配置：**

   ```bash
   # 使用您的设置编辑config.toml
   nano config.toml
   ```

3. **测试配置：**

   ```bash
   # 验证配置
   tello-renewal config-validate

   # 测试邮件通知
   tello-renewal email-test

   # 检查账户状态
   tello-renewal status
   ```

4. **运行续费（先进行干运行）：**

   ```bash
   # 测试续费但不实际执行
   tello-renewal renew --dry-run

   # 执行实际续费
   tello-renewal renew
   ```

## 配置

系统使用 TOML 配置文件。以下是最小配置示例：

```toml
[tello]
email = "your_email@example.com"
password = "your_password"
card_expiration = "1/25"  # MM/YY格式

[smtp]
server = "smtp.gmail.com"
port = 587
username = "your_email@gmail.com"
password = "your_app_password"
from_email = '"Tello Renewal" <your_email@gmail.com>'

[notifications]
email_enabled = true
recipients = ["admin@example.com"]
```

### 配置部分

- **`[tello]`** - Tello 账户凭据和设置
- **`[browser]`** - 浏览器自动化设置
- **`[renewal]`** - 续费行为配置
- **`[smtp]`** - 邮件服务器设置
- **`[notifications]`** - 通知偏好设置
- **`[logging]`** - 日志配置

## CLI 命令

### 基本操作

```bash
# 执行续费
tello-renewal renew [--dry-run]

# 检查账户状态和余额信息
tello-renewal status
```

### 配置管理

```bash
# 创建示例配置
tello-renewal config-init [--output config.toml]

# 验证配置
tello-renewal config-validate
```

### 测试

```bash
# 测试邮件通知
tello-renewal email-test
```

### 选项

- `--config, -c` - 指定配置文件路径
- `--verbose, -v` - 启用详细日志
- `--help` - 显示帮助信息

## 退出代码

| 代码 | 含义     |
| ---- | -------- |
| 0    | 成功     |
| 1    | 一般错误 |
| 2    | 配置错误 |
| 5    | 续费失败 |
| 6    | 无需续费 |

## 定时任务

### Cron 任务

添加到 crontab 以每日运行：

```bash
# 每日上午9点运行
0 9 * * * /path/to/venv/bin/tello-renewal renew

# 带日志记录
0 9 * * * /path/to/venv/bin/tello-renewal renew >> /var/log/tello-renewal.log 2>&1
```

### Systemd 服务

创建 `/etc/systemd/system/tello-renewal.service`：

```ini
[Unit]
Description=Tello Plan Auto Renewal
After=network.target

[Service]
Type=oneshot
User=tello
WorkingDirectory=/opt/tello-renewal
ExecStart=/opt/tello-renewal/venv/bin/tello-renewal renew
```

创建 `/etc/systemd/system/tello-renewal.timer`：

```ini
[Unit]
Description=Run Tello renewal daily
Requires=tello-renewal.service

[Timer]
OnCalendar=daily
Persistent=true

[Install]
WantedBy=timers.target
```

启用并启动：

```bash
sudo systemctl enable tello-renewal.timer
sudo systemctl start tello-renewal.timer
```

## 安全注意事项

- 将敏感配置文件存储为受限权限（600）
- 使用应用密码进行邮件认证
- 考虑加密包含密码的配置文件
- 以最小权限运行
- 定期更新依赖项

## 故障排除

### 常见问题

1. **找不到 WebDriver：**

   ```bash
   # 为Firefox安装geckodriver
   # 在Ubuntu/Debian上：
   sudo apt install firefox-geckodriver

   # 在macOS上：
   brew install geckodriver
   ```

2. **登录失败：**

   - 验证配置中的凭据
   - 检查 Tello 网站结构是否有变化
   - 尝试使用 `--verbose` 运行以获取详细日志

3. **邮件发送失败：**

   - 验证 SMTP 设置
   - 为 Gmail 使用应用密码
   - 使用 `tello-renewal email-test` 进行测试

4. **浏览器自动化问题：**
   - 在配置中尝试不同的浏览器类型
   - 禁用无头模式进行调试
   - 检查浏览器和 WebDriver 版本

### 调试模式

使用详细日志运行以排除问题：

```bash
tello-renewal --verbose renew --dry-run
```

### 日志文件

检查日志文件以获取详细错误信息：

```bash
tail -f tello_renewal.log
```

## Docker 使用

详细的 Docker 使用说明请参见 [`docker/README_zh.md`](docker/README_zh.md) 或 [`docker/README_en.md`](docker/README_en.md)。

### 快速 Docker 开始

```bash
# 使用 Docker 构建和运行
make docker-build
docker run --rm -v $(pwd)/config:/app/config oaklight/tello-renewal:latest

# 或使用提供的脚本
./scripts/run.sh --help
```

### 可用的 Docker 命令

```bash
# 构建基础镜像 (Alpine Python + Selenium + geckodriver)
make docker-build-base
make docker-push-base

# 构建应用镜像
make docker-build
make docker-push

# 清理
make docker-clean
```

## 开发

### 设置开发环境

```bash
# 克隆仓库
git clone <repository-url>
cd tello-renewal

# 创建虚拟环境
python -m venv venv
source venv/bin/activate  # Windows上：venv\Scripts\activate

# 以开发模式安装并包含开发依赖
pip install -e ".[dev]"

# 安装pre-commit钩子
pre-commit install
```

### 运行测试

```bash
# 运行所有测试
pytest

# 运行覆盖率测试
pytest --cov=tello_renewal

# 运行特定测试文件
pytest tests/test_models.py
```

## 贡献

1. Fork 仓库
2. 创建功能分支
3. 进行更改
4. 为新功能添加测试
5. 确保所有测试通过
6. 提交拉取请求

## 许可证

本项目采用 MIT 许可证 - 详情请参阅 LICENSE 文件。

## 免责声明

本软件按原样提供，仅用于教育和自动化目的。用户有责任：

- 确保遵守 Tello 的服务条款
- 维护其凭据的安全性
- 监控续费过程
- 准备备用付款方式

作者不对使用本软件可能产生的任何服务中断、续费失败或其他问题负责。
