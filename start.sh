#!/usr/bin/env bash
set -Eeuo pipefail

PROJECT_NAME="${PROJECT_NAME:-lesson-review}"
ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ACTION="${1:-start}"

cd "$ROOT_DIR"

info() {
  printf "\033[1;34m==>\033[0m %s\n" "$*"
}

warn() {
  printf "\033[1;33m注意:\033[0m %s\n" "$*"
}

fail() {
  printf "\033[1;31m错误:\033[0m %s\n" "$*" >&2
  exit 1
}

usage() {
  cat <<EOF
用法:
  ./start.sh              构建并启动完整系统
  ./start.sh start        构建并启动完整系统
  ./start.sh logs         查看所有服务日志
  ./start.sh status       查看服务状态
  ./start.sh stop         停止服务
  ./start.sh restart      重新构建并启动服务

可选环境变量:
  PROJECT_NAME=lesson-review   Docker Compose 项目名
EOF
}

prepare_docker_config() {
  if [[ -n "${DOCKER_CONFIG:-}" ]]; then
    return
  fi

  local default_config="${HOME}/.docker/config.json"
  if [[ -f "$default_config" ]] && grep -q "desktop" "$default_config"; then
    if ! command -v docker-credential-desktop >/dev/null 2>&1; then
      export DOCKER_CONFIG="${TMPDIR:-/tmp}/lesson-arena-docker-config"
      mkdir -p "$DOCKER_CONFIG"
      if [[ ! -f "$DOCKER_CONFIG/config.json" ]]; then
        printf "{}\n" > "$DOCKER_CONFIG/config.json"
      fi
      warn "检测到 Docker Desktop 凭据助手不可用，已临时使用 $DOCKER_CONFIG"
    fi
  fi
}

detect_compose() {
  if ! command -v docker >/dev/null 2>&1; then
    fail "未找到 docker 命令，请先安装 Docker Desktop 或 Colima + Docker CLI。"
  fi

  if docker compose version >/dev/null 2>&1; then
    COMPOSE_CMD=(docker compose)
  elif command -v docker-compose >/dev/null 2>&1; then
    COMPOSE_CMD=(docker-compose)
  else
    fail "未找到 Docker Compose，请安装 docker compose 插件或 docker-compose。"
  fi
}

docker_is_ready() {
  docker info >/dev/null 2>&1
}

ensure_docker_daemon() {
  if docker_is_ready; then
    return
  fi

  local colima_socket="${HOME}/.colima/default/docker.sock"

  if [[ -S "$colima_socket" ]]; then
    export DOCKER_HOST="unix://${colima_socket}"
    if docker_is_ready; then
      warn "默认 Docker 不可用，已切换到 Colima: $DOCKER_HOST"
      return
    fi
  fi

  if command -v colima >/dev/null 2>&1; then
    info "Docker daemon 未运行，正在启动 Colima..."
    colima start --cpu 4 --memory 4
    if [[ -S "$colima_socket" ]]; then
      export DOCKER_HOST="unix://${colima_socket}"
    fi
    if docker_is_ready; then
      return
    fi
  fi

  fail "Docker daemon 未运行。请先启动 Docker Desktop，或安装并启动 Colima。"
}

compose() {
  "${COMPOSE_CMD[@]}" -p "$PROJECT_NAME" "$@"
}

ensure_env_file() {
  if [[ -f ".env" ]]; then
    return
  fi

  if [[ -f ".env.example" ]]; then
    cp .env.example .env
    warn "未找到 .env，已从 .env.example 创建。正式部署前请检查其中的密钥和密码。"
  else
    fail "未找到 .env 或 .env.example，无法启动后端环境。"
  fi
}

wait_for_http() {
  local name="$1"
  local url="$2"
  local attempts="${3:-60}"

  info "等待 ${name} 就绪: ${url}"
  for _ in $(seq 1 "$attempts"); do
    if curl -fsS "$url" >/dev/null 2>&1; then
      info "${name} 已就绪"
      return
    fi
    sleep 2
  done

  warn "${name} 暂未响应，请运行 ./start.sh logs 查看启动日志。"
}

print_summary() {
  cat <<EOF

系统已启动:
  前端入口:   http://127.0.0.1
  后端 API:   http://127.0.0.1:8000/api/
  Swagger:    http://127.0.0.1:8000/api/docs/swagger/
  管理后台:   http://127.0.0.1:8000/admin/

常用命令:
  ./start.sh logs      查看日志
  ./start.sh status    查看容器状态
  ./start.sh stop      停止服务

EOF
}

start_services() {
  prepare_docker_config
  detect_compose
  ensure_docker_daemon
  ensure_env_file

  info "使用 Docker Compose 项目名: ${PROJECT_NAME}"
  info "构建并启动数据库、Redis、后端、Worker、前端..."
  compose up --build -d

  compose ps
  wait_for_http "后端健康检查" "http://127.0.0.1:8000/api/system/health/"
  wait_for_http "前端页面" "http://127.0.0.1/"
  print_summary
}

prepare_for_compose_action() {
  prepare_docker_config
  detect_compose
  ensure_docker_daemon
}

case "$ACTION" in
  start|up)
    start_services
    ;;
  restart)
    start_services
    ;;
  logs)
    prepare_for_compose_action
    compose logs -f "${@:2}"
    ;;
  status|ps)
    prepare_for_compose_action
    compose ps
    ;;
  stop|down)
    prepare_for_compose_action
    compose down
    ;;
  -h|--help|help)
    usage
    ;;
  *)
    usage
    fail "未知命令: $ACTION"
    ;;
esac
