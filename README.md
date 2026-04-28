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
