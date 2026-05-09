#!/usr/bin/env bash
set -Eeuo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
ENV_FILE="${ROOT_DIR}/.env.cloudbase"

cd "$ROOT_DIR"

if [[ ! -f "$ENV_FILE" ]]; then
  echo "未找到 .env.cloudbase，请先运行: cp .env.cloudbase.example .env.cloudbase" >&2
  exit 1
fi

set -a
# shellcheck disable=SC1090
source "$ENV_FILE"
set +a

if command -v tcb >/dev/null 2>&1; then
  CLI="tcb"
elif command -v cloudbase >/dev/null 2>&1; then
  CLI="cloudbase"
else
  echo "未找到 CloudBase CLI，请先安装: npm install -g @cloudbase/cli" >&2
  exit 1
fi

: "${CLOUDBASE_ENV_ID:?请在 .env.cloudbase 中填写 CLOUDBASE_ENV_ID}"
: "${VITE_API_BASE_URL:?请在 .env.cloudbase 中填写 VITE_API_BASE_URL}"

SERVICE_NAME="${CLOUDBASE_SERVICE_NAME:-lesson-review-api}"
SERVICE_PORT="${PORT:-8000}"
CONFIGURE_API_ROUTE="${CLOUDBASE_CONFIGURE_API_ROUTE:-True}"
REMOVE_LEGACY_API_WILDCARD_ROUTE="${CLOUDBASE_REMOVE_LEGACY_API_WILDCARD_ROUTE:-True}"

is_enabled() {
  case "$(printf '%s' "$1" | tr '[:upper:]' '[:lower:]')" in
    1|true|yes|on) return 0 ;;
    *) return 1 ;;
  esac
}

strip_url_to_domain() {
  local value="$1"
  value="${value#https://}"
  value="${value#http://}"
  value="${value%%/*}"
  printf '%s' "$value"
}

echo "构建前端..."
(
  cd frontend
  VITE_API_BASE_URL="$VITE_API_BASE_URL" npm run build
)

echo "上传前端静态文件..."
FRONTEND_DEPLOY_LOG="$(mktemp "${TMPDIR:-/tmp}/lesson-cloudbase-frontend.XXXXXX")"
"$CLI" hosting deploy frontend/dist / -e "$CLOUDBASE_ENV_ID" 2>&1 | tee "$FRONTEND_DEPLOY_LOG"

FRONTEND_DOMAIN="${CLOUDBASE_FRONTEND_DOMAIN:-}"
if [[ -z "$FRONTEND_DOMAIN" ]]; then
  FRONTEND_SITE_URL="$(
    grep -Eo 'https?://[^[:space:]]+' "$FRONTEND_DEPLOY_LOG" \
      | grep -m1 'tcloudbaseapp\.com' \
      || true
  )"
  if [[ -n "$FRONTEND_SITE_URL" ]]; then
    FRONTEND_DOMAIN="$(strip_url_to_domain "$FRONTEND_SITE_URL")"
  fi
fi
rm -f "$FRONTEND_DEPLOY_LOG"

TMP_DIR="$(mktemp -d "${TMPDIR:-/tmp}/lesson-cloudbase-backend.XXXXXX")"
trap 'rm -rf "$TMP_DIR"' EXIT

mkdir -p "$TMP_DIR/backend" "$TMP_DIR/scripts"
rsync -a \
  --exclude '__pycache__' \
  --exclude '*.pyc' \
  --exclude 'media' \
  --exclude 'staticfiles' \
  --exclude 'db.sqlite3' \
  backend/ "$TMP_DIR/backend/"
rsync -a scripts/ "$TMP_DIR/scripts/"
cp Dockerfile.cloudbase "$TMP_DIR/Dockerfile"
cp "$ENV_FILE" "$TMP_DIR/backend/.env.cloudbase"

echo "部署后端 CloudRun 服务..."
printf '\n' | "$CLI" --env-id "$CLOUDBASE_ENV_ID" cloudrun deploy \
  -s "$SERVICE_NAME" \
  --port "$SERVICE_PORT" \
  --source "$TMP_DIR" \
  --force \
  --installDependency false

if is_enabled "$CONFIGURE_API_ROUTE"; then
  if [[ -z "$FRONTEND_DOMAIN" ]]; then
    echo "未能自动识别前端域名，跳过 /api 路由配置。可在 .env.cloudbase 设置 CLOUDBASE_FRONTEND_DOMAIN 后重试。" >&2
  else
    ROUTE_DATA="$(printf '{"domain":"%s","routes":[{"path":"/api","upstreamResourceType":"CBR","upstreamResourceName":"%s","enable":true,"enableAuth":false,"enableSafeDomain":true,"enablePathTransmission":false}]}' "$FRONTEND_DOMAIN" "$SERVICE_NAME")"
    echo "配置前端域名 /api 路由到 CloudRun 服务: https://${FRONTEND_DOMAIN}/api -> ${SERVICE_NAME}"
    if ! printf 'y\n' | "$CLI" --env-id "$CLOUDBASE_ENV_ID" routes add --data "$ROUTE_DATA"; then
      echo "新增路由失败，尝试更新已有 /api 路由..."
      printf 'y\n' | "$CLI" --env-id "$CLOUDBASE_ENV_ID" routes edit --data "$ROUTE_DATA"
    fi

    if is_enabled "$REMOVE_LEGACY_API_WILDCARD_ROUTE"; then
      echo "清理旧版 /api/* 路由。CloudBase HTTP 服务路由按 /api 前缀匹配。"
      printf 'y\n' | "$CLI" --env-id "$CLOUDBASE_ENV_ID" routes delete "$FRONTEND_DOMAIN" -p '/api/*' || true
    fi
  fi
fi

echo "部署提交完成。请在 CloudBase 控制台确认 CloudRun 版本变为 normal。"
