# CloudBase 部署说明

这个目录记录腾讯云 CloudBase 部署方式。当前项目仍然保留原来的 Docker Compose 本地/云服务器部署；CloudBase 部署是额外新增的一条路径。

## 部署拆分

CloudBase 不是直接运行 `docker-compose.yml` 的云服务器，所以要拆成几块：

- 前端：`frontend` 打包后部署到静态网站托管。
- 后端：Django 使用 `Dockerfile.cloudbase` 部署到云托管。
- 数据库：优先使用 CloudBase SQL / CynosDB 的 MySQL 连接；也可以改用外部 PostgreSQL。
- 上传文件：CloudBase 默认使用数据库存储上传原文和预览 PDF，避免容器重建后 `/app/backend/media` 丢失；文件量明显增大后再考虑改接对象存储或 CFS。
- Worker：首版 CloudBase 部署使用 `CELERY_TASK_ALWAYS_EAGER=True`，让文档解析在后端请求内同步执行，避免单独部署 Redis 和 Celery Worker。

## 文件用途

- `.github/workflows/cloudbase-deploy.yml`：GitHub Actions 部署入口，推送 `main` 或手动触发后部署到腾讯云 CloudBase。
- `cloudbaserc.json`：CloudBase Framework 配置留档。
- `Dockerfile`：腾讯云控制台 Git 仓库构建的默认后端 Dockerfile。
- `Dockerfile.cloudbase`：后端云托管容器镜像构建文件。
- `.env.cloudbase.example`：CloudBase 生产环境变量模板。
- `scripts/cloudbase-deploy.sh`：构建前端、上传静态托管、打包并提交后端 CloudRun 服务；GitHub Actions 和本地备用部署共用这个脚本。
- `.dockerignore` / `Dockerfile.cloudbase.dockerignore`：减少上传和镜像构建体积。

## GitHub Actions 部署

1. 在腾讯云访问管理里创建一个用于部署的 API 密钥，记录 `SecretId` 和 `SecretKey`。

2. 在 GitHub 仓库进入 `Settings -> Secrets and variables -> Actions`，新增这些 Repository secrets：

   ```text
   TCB_ENV_ID=你的CloudBase环境ID
   TCB_SECRET_ID=腾讯云SecretId
   TCB_SECRET_KEY=腾讯云SecretKey
   CLOUDBASE_ENV_FILE=完整的.env.cloudbase内容
   ```

   `CLOUDBASE_ENV_FILE` 可以直接复制 `.env.cloudbase.example`，再把所有生产值改好。至少需要包含：

   ```env
   CLOUDBASE_ENV_ID=你的CloudBase环境ID
   SECRET_KEY=强随机字符串
   DJANGO_SUPERUSER_PASSWORD=强管理员密码
   ALLOWED_HOSTS=你的CloudBase域名或*
   CSRF_TRUSTED_ORIGINS=https://你的CloudBase域名
   CORS_ALLOWED_ORIGINS=https://你的CloudBase域名
   VITE_API_BASE_URL=/api
   CLOUDBASE_CONFIGURE_API_ROUTE=True
   MEDIA_STORAGE_BACKEND=apps.core.storage.DatabaseMediaStorage
   ```

3. 推送到 `main` 分支，或在 GitHub Actions 页面手动运行 `Deploy to Tencent CloudBase`。

4. 部署完成后，进入 CloudBase 控制台确认：

   - 静态网站托管已更新。
   - 云托管 `lesson-review-api` 新版本状态为 `normal`。
   - 前端域名存在 `/api` 路由，且上游指向 `lesson-review-api`。

## 本地备用部署

如果需要从本机临时部署，可以继续使用本地 CLI：

1. 安装 CloudBase CLI。

   ```bash
   npm install -g @cloudbase/cli
   ```

2. 登录腾讯云。

   ```bash
   cloudbase login
   ```

3. 准备环境变量。

   ```bash
   cp .env.cloudbase.example .env.cloudbase
   ```

   打开 `.env.cloudbase`，至少修改：

   ```env
   CLOUDBASE_ENV_ID=你的CloudBase环境ID
   SECRET_KEY=强随机字符串
   DJANGO_SUPERUSER_PASSWORD=强管理员密码
   ALLOWED_HOSTS=你的CloudBase域名或*
   CSRF_TRUSTED_ORIGINS=https://你的CloudBase域名
   CORS_ALLOWED_ORIGINS=https://你的CloudBase域名
   VITE_API_BASE_URL=/api
   CLOUDBASE_CONFIGURE_API_ROUTE=True
   MEDIA_STORAGE_BACKEND=apps.core.storage.DatabaseMediaStorage
   ```

4. 数据库选择。

   默认配置按 CloudBase SQL / CynosDB MySQL 走：

   ```env
   DB_ENGINE=mysql
   MYSQL_DATABASE=lesson_review
   ```

   如果你是在控制台手动创建 SQL 数据库，就把控制台里的连接信息填入 `.env.cloudbase`。

   如果你使用腾讯云 PostgreSQL 或其他 PostgreSQL，改成：

   ```env
   DB_ENGINE=postgres
   POSTGRES_DB=lesson_review
   POSTGRES_HOST=数据库地址
   POSTGRES_PORT=5432
   POSTGRES_USER=数据库用户
   POSTGRES_PASSWORD=数据库密码
   ```

5. 部署。

   项目脚本会自动读取 `.env.cloudbase`：

   ```bash
   ./scripts/cloudbase-deploy.sh
   ```

## 控制台部署路径

如果不用 CLI，也可以在控制台手动做：

1. 静态网站托管：进入 `frontend`，用 `VITE_API_BASE_URL=/api npm run build` 构建，上传 `frontend/dist`。
2. 云托管：源码目录选项目根目录，Dockerfile 选 `Dockerfile.cloudbase`，服务端口填 `8000`，访问路径填 `/api`。
3. HTTP 访问服务：给前端静态托管域名添加 `/api` 前缀路由，上游资源类型选 `CBR`，上游服务选后端 CloudRun 服务。
4. SQL 型数据库：创建 MySQL 数据库，把连接信息填到云托管环境变量。
5. 持久化文件：默认使用 `MEDIA_STORAGE_BACKEND=apps.core.storage.DatabaseMediaStorage` 存入数据库。大文件或高频使用场景再改为对象存储或 CFS。

## 访问路径

前端通过同域 `/api` 请求后端，部署脚本会自动把前端静态托管域名的 `/api` 前缀路由到 CloudRun 服务：

```text
VITE_API_BASE_URL=/api
```

这样删除并重建 CloudRun 服务后，不需要手动复制新的直连域名。

后端同时兼容两种路径：

- `/api/system/health/`
- `/system/health/`

上传文件默认 URL：

```text
/api/media/
```

CloudBase 环境默认配置：

```env
MEDIA_STORAGE_BACKEND=apps.core.storage.DatabaseMediaStorage
```

如果之前使用容器本地 `/app/backend/media` 上传过文件，重新部署或容器重建后旧文件可能已经丢失。数据库里的批次记录会保留，但对应 PDF/原文会返回 404；这种旧批次需要重新上传。

前端使用 hash 路由，CloudBase 静态托管访问形如：

```text
https://你的前端域名/#/login
```

## 后续正式化建议

- 把 `ALLOWED_HOSTS=*` 改成实际域名。
- 配置自定义域名和 HTTPS。
- 如果 Word/PDF 解析请求变慢，再单独拆 Redis + Celery Worker。
- 定期备份 SQL 数据库；如果后续改用 CFS 或对象存储，也要同步备份文件存储。
