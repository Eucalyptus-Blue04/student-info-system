# 学籍信息管理系统

> 基于 Flask 框架开发的高校学籍信息管理系统，支持管理员、教师、学生三种角色，提供完整的学籍生命周期管理功能。

## ✨ 功能特性

- **用户认证与权限控制** — 基于 Flask-Login 的 RBAC 三级权限体系（管理员/教师/学生）
- **组织架构管理** — 院系、专业、年级、班级的层级管理
- **学生信息管理** — 学生信息的增删改查及批量导入
- **学籍状态管理** — 在读、休学、退学、毕业、结业等状态流转及历史记录
- **转专业审批** — 学生发起转专业申请，教师/管理员审批流程
- **异步任务队列** — 基于 Celery + Redis 的后台任务（通知、导入、报表）
- **安全机制** — 图形验证码、请求限流、环境变量配置
- **容器化部署** — Docker + Nginx + Gunicorn 一键部署

## 🛠 技术栈

| 层级 | 技术 |
|------|------|
| 后端框架 | Python 3.11+ / Flask 3.0 |
| 数据库 | SQLite（开发）/ SQLAlchemy ORM |
| 数据库迁移 | Flask-Migrate / Alembic |
| 任务队列 | Celery 5.3 / Redis |
| 缓存 | Flask-Caching / Redis |
| 前端模板 | Jinja2 / Bootstrap 5 |
| 用户认证 | Flask-Login |
| 测试 | pytest / pytest-cov |
| 部署 | Docker / Docker Compose / Nginx / Gunicorn |

## 🚀 快速开始

### 环境要求

- Python 3.11+
- Redis（可选，用于异步任务和缓存）

### 本地开发

```bash
# 1. 克隆仓库
git clone https://github.com/<your-username>/student-info-system.git
cd student-info-system

# 2. 创建虚拟环境
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# 3. 安装依赖
pip install -r requirements.txt

# 4. 初始化数据库
python reset_db.py

# 5. （可选）导入测试数据
python test_data.py

# 6. 启动开发服务器
python app.py
```

访问 http://localhost:5000，使用默认管理员账号登录：

| 角色 | 用户名 | 密码 |
|------|--------|------|
| 管理员 | admin | admin |

### Docker 部署

```bash
# 启动所有服务（Web + Nginx + Celery Worker + Celery Beat + Redis）
docker-compose up -d --build

# 查看日志
docker-compose logs -f

# 停止服务
docker-compose down
```

## 📁 项目结构

```
├── app.py                 # Flask 应用主文件（路由、认证、RBAC）
├── db.py                  # SQLAlchemy 数据库模型定义
├── config.py              # 多环境配置管理（Dev/Prod/Test）
├── tasks.py               # Celery 异步任务（通知、导入、报表）
├── celery_worker.py       # Celery 工厂函数
├── logging_config.py      # 日志配置（RotatingFileHandler）
├── get_captcha.py         # 图形验证码生成
├── init_admin.py          # 默认管理员账号初始化
├── reset_db.py            # 数据库重置工具
├── test_data.py           # 测试数据生成脚本
├── conftest.py            # pytest 测试固件
├── requirements.txt       # Python 依赖清单
├── Makefile               # 常用开发命令
├── Dockerfile             # Docker 镜像构建
├── docker-compose.yml     # 多服务编排配置
├── nginx.conf             # Nginx 反向代理配置
├── pytest.ini             # 测试配置
├── .env.example           # 环境变量模板
├── templates/             # Jinja2 HTML 模板
│   ├── base.html          # 基础布局模板
│   ├── login.html         # 登录页
│   ├── students.html      # 学生列表
│   └── ...                # 其他页面模板
├── tests/                 # 自动化测试
│   ├── test_models.py     # 模型单元测试
│   └── test_routes.py     # 路由集成测试
└── migrations/            # Alembic 数据库迁移文件
```

## ⚙️ 环境变量

复制 `.env.example` 为 `.env` 并按需修改：

```bash
cp .env.example .env
```

| 变量 | 说明 | 默认值 |
|------|------|--------|
| `SECRET_KEY` | Flask 会话密钥 | 内置默认值（生产环境请修改） |
| `DATABASE_URL` | 数据库连接字符串 | `sqlite:///students.db` |
| `REDIS_URL` | Redis 连接地址 | `redis://localhost:6379/0` |
| `FLASK_ENV` | 运行环境 | `development` |

## 🧪 测试

```bash
# 运行全部测试
pytest

# 运行测试并生成覆盖率报告
pytest --cov=. --cov-report=html

# 运行指定测试文件
pytest tests/test_models.py
pytest tests/test_routes.py
```

## 📋 常用命令

```bash
# 开发
make run              # 启动开发服务器
make test             # 运行测试
make test-cov         # 运行测试（含覆盖率）

# 数据库
make migrate          # 初始化迁移
make migrate-upgrade  # 执行迁移
make init-db          # 重置数据库

# Docker
make docker-up        # 启动容器
make docker-down      # 停止容器

# Celery
make celery-worker    # 启动 Worker
make celery-beat      # 启动 Beat
```

## 📄 许可证

本项目基于 [MIT License](LICENSE) 开源。
