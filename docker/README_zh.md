# Docker 指南

[中文版](README_zh.md) | [English Version](README_en.md)

本文档介绍如何使用 Docker 运行 Tello Renewal 系统，并提供可重用基础镜像的相关信息。

## 🐳 镜像特性

- **基础镜像**: Alpine Linux (最小化)
- **Python版本**: 3.11
- **浏览器**: Firefox + Geckodriver
- **镜像大小**: ~150MB (预估)
- **安全性**: 非root用户运行
- **资源限制**: 内存512MB，CPU 0.5核

## 📋 前置要求

- Docker 20.10+
- Docker Compose 2.0+ (可选)
- 至少 512MB 可用内存

## 🏗️ 基础镜像

### Alpine Python Gecko 基础镜像

`base.Dockerfile` 创建了一个可重用的基础镜像，包含：

- **Alpine Linux** - 最小化、安全的基础操作系统
- **Python 3.11** - 最新稳定版 Python
- **Firefox** - 用于 web 自动化的无头浏览器
- **Geckodriver** - Firefox 的 WebDriver
- **Selenium** - 预装的 web 自动化框架
- **非 root 用户** - 安全最佳实践

#### 镜像详情

- **镜像名称**: `oaklight/alpine-python-gecko:latest`
- **基础镜像**: `python:3.11-alpine`
- **用户**: `appuser` (UID: 1000, GID: 1000)
- **工作目录**: `/app`
- **环境变量**:
  - `DISPLAY=:99`
  - `MOZ_HEADLESS=1`

#### 预装依赖

基础镜像包含以下 Python 包：

- `selenium>=4.15.0` - Web 自动化框架

#### 构建基础镜像

```bash
# 构建基础镜像
make docker-build-base

# 推送到 DockerHub
make docker-push-base
```

#### 在其他项目中使用

```dockerfile
FROM oaklight/alpine-python-gecko:latest

# 切换到 root 用户进行安装
USER root

# 安装你的 Python 依赖
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# 复制你的应用程序
COPY . .
RUN chown -R appuser:appuser /app

# 切换回非 root 用户
USER appuser

# 你的应用程序命令
CMD ["python", "your-app.py"]
```

#### 优势

1. **一致性** - 所有项目使用相同环境
2. **更快构建** - 基础依赖已预装
3. **安全性** - 非 root 用户和最小攻击面
4. **可重用性** - 可用于多个 web 自动化项目
5. **易维护** - 在单一位置更新通用依赖
6. **即用型** - Selenium 预装并可直接用于 web 自动化

#### Geckodriver 版本

当前 geckodriver 版本为 `0.36.0`。要更新：

1. 修改 `base.Dockerfile` 中的 `GECKODRIVER_VERSION` 参数
2. 重新构建并推送基础镜像
3. 更新依赖项目使用新的基础镜像

## 🚀 快速开始

### 1. 构建镜像

```bash
# 首先构建基础镜像
make docker-build-base

# 构建应用镜像
make docker-build

# 或使用构建脚本
./scripts/build.sh
```

### 2. 准备配置

```bash
# 创建目录
mkdir -p config logs

# 创建配置文件
tello-renewal config-init --output config/config.toml
# 编辑配置文件
nano config/config.toml
```

### 3. 运行容器

```bash
# 使用运行脚本 (推荐)
./scripts/run.sh

# 或使用 docker-compose
docker-compose up tello-renewal

# 或直接使用 docker run
docker run --rm \
  -v $(pwd)/config:/app/config:ro \
  -v $(pwd)/logs:/app/logs \
  oaklight/tello-renewal:latest \
  tello-renewal --config /app/config/config.toml renew
```

## 📖 使用方法

### 基本命令

```bash
# 执行续费
./scripts/run.sh

# 干运行模式 (测试)
./scripts/run.sh --dry-run

# 检查账户状态
./scripts/run.sh --command status

# 验证配置
./scripts/run.sh --command config-validate

# 测试邮件通知
./scripts/run.sh --command email-test
```

### Docker Compose 方式

```bash
# 单次运行
docker-compose up tello-renewal

# 后台运行
docker-compose up -d tello-renewal

# 查看日志
docker-compose logs -f tello-renewal

# 停止容器
docker-compose down
```

### 定时任务模式

```bash
# 启动定时任务 (每天9点运行)
docker-compose --profile scheduler up -d tello-scheduler

# 自定义时间 (每天6点)
CRON_SCHEDULE="0 6 * * *" docker-compose --profile scheduler up -d tello-scheduler

# 查看定时任务日志
docker-compose logs -f tello-scheduler
```

## ⚙️ 配置说明

### 目录结构

```
project/
├── config/
│   └── config.toml          # 主配置文件
├── logs/                    # 日志输出目录
├── scripts/                 # 运行脚本
├── docker-compose.yml       # Docker Compose 配置
└── docker/
    ├── Dockerfile          # 应用镜像定义
    ├── base.Dockerfile     # 基础镜像定义
    └── requirements.txt    # 基础依赖
```

### 环境变量

| 变量名 | 默认值 | 说明 |
|--------|--------|------|
| `TZ` | `America/Chicago` | 时区设置 |
| `CRON_SCHEDULE` | `0 9 * * *` | 定时任务时间 |
| `CONFIG_FILE` | `/app/config/config.toml` | 配置文件路径 |

### 配置文件示例

```toml
[tello]
email = "your_email@example.com"
password = "your_password"
card_expiration = "1/25"  # MM/YY format

[browser]
browser_type = "firefox"
headless = true
window_size = "1920x1080"

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

## 🔧 故障排除

### 常见问题

1. **配置文件未找到**
   ```bash
   # 检查配置文件路径
   ls -la config/
   # 确保 config.toml 存在
   ```

2. **浏览器启动失败**
   ```bash
   # 检查容器日志
   docker-compose logs tello-renewal
   # 确保有足够内存
   ```

3. **权限问题**
   ```bash
   # 检查目录权限
   chmod 755 config logs
   chmod 644 config/config.toml
   ```

### 调试模式

```bash
# 启用详细日志
docker run --rm \
  -v $(pwd)/config:/app/config:ro \
  -v $(pwd)/logs:/app/logs \
  oaklight/tello-renewal:latest \
  tello-renewal --config /app/config/config.toml --verbose renew --dry-run

# 进入容器调试
docker run -it --rm \
  -v $(pwd)/config:/app/config:ro \
  oaklight/tello-renewal:latest \
  sh
```

## 🔒 安全建议

1. **配置文件权限**
   ```bash
   chmod 600 config/config.toml  # 仅所有者可读写
   ```

2. **使用应用密码**
   - Gmail: 使用应用专用密码
   - 避免使用主账户密码

3. **网络隔离**
   ```yaml
   # docker-compose.yml 中添加
   networks:
     - tello-network
   ```

4. **定期更新**
   ```bash
   # 更新镜像
   docker pull python:3.11-alpine
   make docker-build-base
   make docker-build
   ```

## 📊 监控和日志

### 日志文件

- `logs/tello_renewal.log` - 应用日志
- `logs/cron.log` - 定时任务日志

### 健康检查

```bash
# 检查容器状态
docker-compose ps

# 查看健康状态
docker inspect tello-renewal | grep Health -A 10
```

### 资源监控

```bash
# 查看资源使用
docker stats tello-renewal

# 查看容器信息
docker inspect tello-renewal
```

## 🔄 更新和维护

### 更新应用

```bash
# 重新构建镜像
make docker-build-base
make docker-build

# 重启容器
docker-compose down
docker-compose up -d tello-renewal
```

### 备份配置

```bash
# 备份配置和日志
tar -czf tello-backup-$(date +%Y%m%d).tar.gz config/ logs/
```

### 清理

```bash
# 清理未使用的镜像
docker image prune

# 清理所有未使用资源
docker system prune -a

# 使用 Makefile 清理
make docker-clean
```

## 📞 支持

如果遇到问题，请：

1. 检查日志文件
2. 确认配置正确
3. 查看 GitHub Issues
4. 提交新的 Issue 并附上日志

---

**注意**: 请确保遵守 Tello 的服务条款，并负责任地使用此自动化工具。