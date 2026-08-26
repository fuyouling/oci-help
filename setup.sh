#!/usr/bin/env bash
#
# setup.sh - 快速后台启动 oci-help 服务
#
# 用途：在已执行过 setup_init.sh 的服务器上，快速将 oci-help 以
#       后台进程方式运行（持续轮询 monitor 模式）。
#
# 使用方法：
#   bash setup.sh              # 默认后台启动 monitor
#   bash setup.sh start        # 同默认
#   bash setup.sh status       # 查看运行状态
#   bash setup.sh stop         # 停止
#   bash setup.sh restart      # 重启
#   bash setup.sh logs         # 跟踪日志
#
# 说明：
#   - 使用虚拟环境中的可执行文件，无需手动激活环境。
#   - 日志写入 run/oci-help.log，PID 写入 run/oci-help.pid。
#
set -euo pipefail

cd "$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

VENV_DIR=".venv"
BIN="$VENV_DIR/bin/oci-help"
RUN_DIR="run"
LOG_FILE="$RUN_DIR/oci-help.log"
PID_FILE="$RUN_DIR/oci-help.pid"

# 传递给 oci-help 的参数（默认持续轮询）
APP_ARGS=("monitor")

is_running() {
    [ -f "$PID_FILE" ] || return 1
    local pid
    pid="$(cat "$PID_FILE" 2>/dev/null || echo)"
    [ -n "$pid" ] && kill -0 "$pid" 2>/dev/null
}

do_start() {
    if is_running; then
        echo "oci-help 已在运行 (PID $(cat "$PID_FILE"))。"
        return 0
    fi

    if [ ! -x "$BIN" ]; then
        echo "未找到可执行文件：$BIN" >&2
        echo "请先运行：bash setup_init.sh" >&2
        exit 1
    fi

    mkdir -p "$RUN_DIR"
    echo "==> 后台启动 oci-help（日志：$LOG_FILE）"
    nohup "$BIN" "${APP_ARGS[@]}" >> "$LOG_FILE" 2>&1 &
    echo $! > "$PID_FILE"
    sleep 1
    if is_running; then
        echo "    启动成功，PID $(cat "$PID_FILE")。"
    else
        echo "    启动失败，请查看日志：$LOG_FILE" >&2
        exit 1
    fi
}

do_stop() {
    if ! is_running; then
        echo "oci-help 未运行。"
        rm -f "$PID_FILE"
        return 0
    fi
    local pid
    pid="$(cat "$PID_FILE")"
    echo "==> 停止 oci-help (PID $pid)"
    kill "$pid" 2>/dev/null || true
    for _ in $(seq 1 10); do
        kill -0 "$pid" 2>/dev/null || break
        sleep 0.5
    done
    if kill -0 "$pid" 2>/dev/null; then
        echo "    未正常退出，强制终止。"
        kill -9 "$pid" 2>/dev/null || true
    fi
    rm -f "$PID_FILE"
    echo "    已停止。"
}

do_status() {
    if is_running; then
        echo "oci-help 正在运行 (PID $(cat "$PID_FILE"))"
    else
        echo "oci-help 未运行。"
        return 1
    fi
}

do_logs() {
    if [ ! -f "$LOG_FILE" ]; then
        echo "暂无日志文件：$LOG_FILE" >&2
        exit 1
    fi
    tail -f "$LOG_FILE"
}

case "${1:-start}" in
    start)   do_start ;;
    stop)    do_stop ;;
    restart) do_stop; do_start ;;
    status)  do_status ;;
    logs)    do_logs ;;
    *)
        echo "用法：$0 {start|stop|restart|status|logs}" >&2
        exit 1
        ;;
esac
