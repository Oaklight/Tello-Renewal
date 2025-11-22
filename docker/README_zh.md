# Docker 指南

[中文版](README_zh.md) | [English Version](README_en.md)

本文档介绍如何使用 Docker 运行 Tello Renewal 系统，并提供可重用基础镜像的相关信息。

## 🐳 镜像特性

- **基础镜像**: Alpine Linux (最小化)
- **Python 版本**: 3.11
- **浏览器**: Firefox + Geckodriver
- **镜像大小**: ~831MB (基础镜像)
- **安全性**: 非 root 用户运行
- **资源限制**: 内存 512MB，CPU 0.5 核

## 📋 前置要求

- Docker 20.10+
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

- `selenium>=4.27.0` - Web 自动化框架

#### 构建基础镜像

```bash
# 构建基础镜像
make build-docker-base

# 推送到 DockerHub
make push-docker-base
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
make build-docker-base

# 构建应用镜像（自动检测版本）
make build-docker

# 或直接使用构建脚本
./scripts/build.sh

# 使用指定版本构建
make build-docker V=1.0.0

# 使用 PyPI 镜像构建
make build-docker MIRROR=https://pypi.tuna.tsinghua.edu.cn/simple

# 同时指定版本和镜像
make build-docker V=1.0.0 MIRROR=https://mirrors.cernet.edu.cn/pypi/web/simple
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

### 3. 下载并运行

```bash
# 下载运行脚本
curl -o run.sh https://raw.githubusercontent.com/Oaklight/Tello-Renewal/refs/heads/master/scripts/run.sh
chmod +x run.sh

# 使用运行脚本 (推荐)
./run.sh renew

# 或直接使用 docker run
docker run --rm \
  -v ~/.config/tello-renewal:/app/config:ro \
  -v ./logs:/app/logs \
  -e TZ=America/Chicago \
  oaklight/tello-renewal:latest \
  tello-renewal --config /app/config/config.toml renew
```

### 备用下载地址

如果 GitHub 无法访问，可使用以下镜像地址：

```bash
# JSDelivr CDN
curl -o run.sh https://cdn.jsdelivr.net/gh/Oaklight/Tello-Renewal@master/scripts/run.sh

# JSDelivr 镜像
curl -o run.sh https://cdn.jsdmirror.com/gh/Oaklight/Tello-Renewal@master/scripts/run.sh
```

## 📖 使用方法

### 基本命令

```bash
# 执行续费
./run.sh renew

# 干运行模式 (测试)
./run.sh renew --dry-run

# 检查账户状态
./run.sh status

# 验证配置
./run.sh config-validate

# 测试邮件通知
./run.sh email-test

# 创建示例配置
./run.sh config-init --output ~/.config/tello-renewal/config.toml
```

### 使用 Cron 定时任务

使用系统 cron 设置自动续费：

```bash
# 编辑 crontab
crontab -e

# 添加每日9点续费任务 (根据需要调整路径)
0 9 * * * /path/to/run.sh renew >> /var/log/tello-renewal-cron.log 2>&1

# 或每周日9点续费
0 9 * * 0 /path/to/run.sh renew >> /var/log/tello-renewal-cron.log 2>&1
```

### 高级 Cron 设置

```bash
# 创建专用的 cron 脚本
cat > /usr/local/bin/tello-renewal-cron.sh << 'EOF'
#!/bin/bash
cd /path/to/your/project
./run.sh renew
EOF

chmod +x /usr/local/bin/tello-renewal-cron.sh

# 添加到 crontab
echo "0 9 * * * /usr/local/bin/tello-renewal-cron.sh" | crontab -
```

## ⚙️ 配置说明

### 目录结构

```
project/
├── ~/.config/tello-renewal/
│   └── config.toml          # 主配置文件
├── logs/                    # 日志输出目录
└── run.sh                   # 运行脚本
```

### 环境变量

| 变量名        | 默认值                    | 说明         |
| ------------- | ------------------------- | ------------ |
| `TZ`          | `America/Chicago`         | 时区设置     |
| `CONFIG_FILE` | `/app/config/config.toml` | 配置文件路径 |

### Makefile 变量

| 变量名   | 默认值                             | 说明                          |
| -------- | ---------------------------------- | ----------------------------- |
| `V`      | 从 PyPI 或 pyproject.toml 自动检测 | Docker 镜像版本标签           |
| `MIRROR` | (空)                               | PyPI 镜像 URL，用于加速包安装 |

#### 版本检测机制

构建系统按以下顺序自动检测版本：

1. **本地 wheel 文件** - 如果存在 `dist/*.whl`，使用 wheel 文件名中的版本
2. **指定版本** - 如果指定了 `V=x.x.x`，使用该版本
3. **PyPI 最新版** - 从 PyPI 获取最新版本
4. **本地回退** - 如果 PyPI 不可用，使用 `pyproject.toml` 中的版本

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
   # 检查日志目录
   ls -la logs/
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
   make build-docker-base
   make build-docker
   ```

## 📊 监控和日志

### 日志文件

- `logs/tello_renewal.log` - 应用日志
- `logs/cron.log` - 定时任务日志

### 健康检查

```bash
# 查看最近日志
tail -f logs/tello_renewal.log

# 查看 cron 日志
tail -f /var/log/tello-renewal-cron.log
```

### 资源监控

```bash
# 查看执行期间的 Docker 资源使用
docker stats

# 检查系统资源
htop
```

## 🔄 更新和维护

### 更新应用

```bash
# 拉取最新基础镜像并重新构建
docker pull python:3.11-alpine
make build-docker-base
make build-docker

# 或更新到指定版本
make build-docker V=1.2.0

# 更新运行脚本
curl -o run.sh https://raw.githubusercontent.com/Oaklight/Tello-Renewal/refs/heads/master/scripts/run.sh
chmod +x run.sh
```

### 包管理

```bash
# 构建 Python 包
make build-package

# 推送包到 PyPI
make push-package

# 清理包构建文件
make clean-package
```

### 备份配置

```bash
# 备份配置和日志
tar -czf tello-backup-$(date +%Y%m%d).tar.gz ~/.config/tello-renewal/ logs/
```

### 清理

```bash
# 清理未使用的镜像
docker image prune

# 清理所有未使用资源
docker system prune -a

# 使用 Makefile 清理
make clean-docker
```

## 📞 支持

如果遇到问题，请：

1. 检查日志文件
2. 确认配置正确
3. 查看 GitHub Issues
4. 提交新的 Issue 并附上日志

---

**注意**: 请确保遵守 Tello 的服务条款，并负责任地使用此自动化工具。
