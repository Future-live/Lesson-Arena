# 教案评价系统

一个面向真实部署的完整教案上传、展示与评价系统。系统要求用户一次上传一组双教案，支持 `doc / docx / pdf / txt / md / markdown`，其中 `pdf / doc / docx` 优先保留原始版式展示，避免因文本抽取导致表格、图片和排版失真。

## 架构说明

- 后端：Django 5 + Django REST Framework + Simple JWT + Celery + Redis + PostgreSQL
- 前端：React + TypeScript + Vite + React Query
- 部署：Docker Compose + Nginx + Gunicorn
- 运维能力：健康检查、环境变量配置、自动迁移、静态资源收集、可选自动创建管理员

## 已实现功能

- 用户注册、登录、获取当前用户信息
- 双教案成组上传，严格限制每组必须为 2 份文档
- 文档格式校验与异步解析
- PDF 直接嵌入展示，Word 文档通过 LibreOffice 转换为 PDF 版式预览
- 教案原文下载、双栏对照查看、单教案聚焦放大查看
- 全员互评机制：上传者也可以对自己提交的批次进行评价，其他用户同样可提交或更新评价
- 多维评价模型：目标对齐、内容结构、活动设计、评价反馈、参与包容、语言规范、创新落地
- 评价聚合：总分均分、维度均分、推荐结论分布、最近评价列表
- 盲评控制：管理员和上传者可见汇总评价，其他用户在非本人批次中不可见
- 工作台：待评任务、我的上传、高分批次、最新批次
- Django Admin 后台

## 本地开发

### 后端

```bash
source /Users/future/myenv/bin/activate
cd backend
python manage.py migrate
python manage.py runserver
```

默认使用 SQLite。若希望本地不依赖 Redis 也能体验上传解析，可在环境变量中设置：

```bash
export CELERY_TASK_ALWAYS_EAGER=True
```

如果你要在本机直接体验 `doc / docx` 的保版式预览，本机还需要安装 LibreOffice；Docker 部署镜像里已经内置。

### 前端

```bash
cd frontend
npm install
npm run dev
```

默认前端地址：`http://127.0.0.1:5173`

## Docker 部署

一键启动完整系统：

```bash
./start.sh
```

常用管理命令：

```bash
./start.sh status
./start.sh logs
./start.sh stop
```

如果希望手动使用 Docker Compose，也可以运行：

```bash
cp .env.example .env
docker compose up --build
```

部署完成后：

- 前端入口：`http://127.0.0.1`
- 后端 API：`http://127.0.0.1:8000/api/`
- Swagger：`http://127.0.0.1:8000/api/docs/swagger/`
- Django Admin：`http://127.0.0.1:8000/admin/`

默认管理员账号可通过环境变量控制。当前模板默认值为：

- 用户名：`admin`
- 密码：`admin`

## 关键业务规则

- 每个批次必须上传 2 份教案
- 支持解析格式：`.doc`、`.docx`、`.pdf`、`.txt`、`.md`、`.markdown`
- 教案解析完成前不可评价
- 上传者可以评价自己上传的批次
- 管理员和上传者可以查看批次汇总；其他用户看不到非本人上传批次的汇总与最近评价
- 其他用户对同一批次只保留 1 条评价记录，但可以重复编辑更新

## 建议上线配置

- 将 `DEBUG=False`
- 替换 `SECRET_KEY`
- 使用独立 PostgreSQL/Redis 服务
- 将 `ALLOWED_HOSTS`、`CSRF_TRUSTED_ORIGINS` 设置为正式域名
- 将媒体目录挂载到持久化磁盘或对象存储

## GitHub 部署到腾讯云 CloudBase

本项目已补充腾讯云 CloudBase 适配文件，但 CloudBase 不能直接运行 `docker-compose.yml`，需要拆分部署：

- 前端：CloudBase 静态网站托管
- 后端：CloudBase 云托管，使用根目录 `Dockerfile.cloudbase`
- 数据库：CloudBase SQL / CynosDB MySQL，或外部 PostgreSQL
- 上传文件：CloudBase 默认使用数据库存储上传原文和预览 PDF，避免容器重建后文件丢失；后续也可改接 CFS/对象存储
- 文档解析：首版建议 `CELERY_TASK_ALWAYS_EAGER=True`，先不单独部署 Redis + Celery Worker

相关文件：

- `.github/workflows/cloudbase-deploy.yml`
- `Dockerfile`
- `cloudbaserc.json`
- `.env.cloudbase.example`
- `Dockerfile.cloudbase`
- `deploy/cloudbase/README.md`
- `scripts/cloudbase-deploy.sh`

推荐使用 GitHub Actions 部署。先在 GitHub 仓库 `Settings -> Secrets and variables -> Actions` 添加：

- `TCB_ENV_ID`：CloudBase 环境 ID
- `TCB_SECRET_ID`：腾讯云 API 密钥 SecretId
- `TCB_SECRET_KEY`：腾讯云 API 密钥 SecretKey
- `CLOUDBASE_ENV_FILE`：按 `.env.cloudbase.example` 填好的完整生产环境变量内容

之后推送到 `main` 分支，或在 Actions 页面手动运行 `Deploy to Tencent CloudBase` workflow，即可部署前端静态托管和后端云托管。

本地 CLI 部署仍可作为备用路径：

```bash
cp .env.cloudbase.example .env.cloudbase
cloudbase login
./scripts/cloudbase-deploy.sh
```

CloudBase 静态托管下前端使用 hash 路由，访问地址类似 `https://你的前端域名/#/login`。
部署脚本默认使用同域 `/api`，并自动给前端域名配置 `/api` 前缀到 CloudRun 服务的路由，因此重建后端服务时通常不需要手动复制 CloudRun 直连域名。
