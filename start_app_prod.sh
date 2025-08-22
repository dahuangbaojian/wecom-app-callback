#!/bin/bash

# 生产环境管理脚本
# 用法: ./manage_production.sh [start|stop|restart|status|logs]

set -e

# 项目根目录和应用配置
PROJECT_ROOT=$(dirname "$(readlink -f "$0")")
APP_NAME="ai_smart_assistant.main:app"

cd "$PROJECT_ROOT"

# 日志函数
log() {
    echo "[$(date +'%Y-%m-%d %H:%M:%S')] $1"
}

log "项目根目录: $PROJECT_ROOT"
log "应用名称: $APP_NAME"

# 加载环境变量
load_env() {
    local env_file="$1"
    local var_name="$2"
    local default_value="$3"
    
    if [ -f "$env_file" ]; then
        local value=$(grep "^$var_name=" "$env_file" | cut -d '=' -f2 | tr -d '"' | tr -d "'" | tr -d ' ')
        if [ -n "$value" ]; then
            echo "$value"
            return
        fi
    fi
    
    echo "$default_value"
}

# 从.env文件加载配置
if [ -f ".env" ]; then
    PORT=$(load_env ".env" "PORT" "8000")
    WORKERS=$(load_env ".env" "WORKERS" "4")
    LOG_DIR=$(load_env ".env" "LOG_DIR" "logs")
else
    PORT="8000"
    WORKERS="4"
    LOG_DIR="logs"
fi

# 获取进程PID列表
get_pids() {
    ps aux | grep "gunicorn.*$APP_NAME.*$PORT" | grep -v grep | awk '{print $2}'
}

# 获取主进程PID
get_pid() {
    get_pids | head -1
}

# 检查服务状态
check_status() {
    local pid=$(get_pid)
    if [ -n "$pid" ]; then
        echo "✅ 服务正在运行 (PID: $pid, 端口: $PORT)"
        return 0
    else
        echo "❌ 服务未运行"
        return 1
    fi
}

# 启动服务
start_service() {
    log "正在启动服务..."
    
    # 检查是否已有实例在运行
    if check_status > /dev/null 2>&1; then
        log "警告: 服务已在运行"
        read -p "是否重启服务? (y/n): " restart
        if [ "$restart" != "y" ]; then
            log "操作取消"
            return
        fi
        stop_service
    fi
    
    # 激活虚拟环境
    if [ -d "venv" ]; then
        log "激活虚拟环境"
        source venv/bin/activate
        log "Python 路径: $(which python)"
        log "Python 版本: $(python --version)"
    else
        log "警告: 未找到虚拟环境 venv/"
        log "Python 路径: $(which python)"
        log "Python 版本: $(python --version)"
    fi
    
    # 安装项目
    log "安装项目"
    if ! pip install -e .; then
        log "❌ 项目安装失败"
        exit 1
    fi
    
    # 确保依赖已安装
    log "安装依赖"
    if ! pip install -r requirements.txt; then
        log "❌ 依赖安装失败"
        exit 1
    fi
    
    # 确保日志目录存在
    mkdir -p "$LOG_DIR"
    log "日志目录: $LOG_DIR"
    
    # 启动服务
    log "正在启动服务 $APP_NAME 在端口 $PORT，工作进程数: $WORKERS"
    
    # 使用 Gunicorn 启动应用
    if ! gunicorn "$APP_NAME" \
        --workers "$WORKERS" \
        --worker-class uvicorn.workers.UvicornWorker \
        --bind "0.0.0.0:$PORT" \
        --timeout 60 \
        --graceful-timeout 30 \
        --pid "${LOG_DIR}/gunicorn.pid" \
        --daemon; then
        log "❌ Gunicorn 启动失败"
        exit 1
    fi
    
    # 检查启动是否成功
    sleep 2
    if check_status > /dev/null 2>&1; then
        log "✅ 服务已成功启动"
        log "📊 使用 './start_assistant_prod.sh status' 查看状态"
        log "📋 使用 './start_assistant_prod.sh logs' 查看日志"
    else
        log "❌ 服务启动失败，请检查日志"
        exit 1
    fi
}

# 停止服务
stop_service() {
    log "正在停止服务..."
    
    # 获取所有相关进程PID
    local pids=$(get_pids)
    
    if [ -z "$pids" ]; then
        log "未找到运行中的服务"
        return
    fi
    
    # 显示找到的进程
    log "发现以下 Gunicorn 进程:"
    echo "$pids" | while read pid; do
        echo "  PID: $pid"
    done
    
    # 优雅地停止所有进程 (发送 TERM 信号)
    log "正在停止所有进程..."
    echo "$pids" | while read pid; do
        kill -TERM $pid 2>/dev/null || true
    done
    
    # 等待进程结束
    log "等待服务停止..."
    for i in {1..15}; do
        local remaining_pids=$(get_pids)
        if [ -z "$remaining_pids" ]; then
            log "✅ 服务已成功停止"
            return
        fi
        sleep 1
    done
    
    # 如果进程仍在运行，强制终止
    local remaining_pids=$(get_pids)
    if [ -n "$remaining_pids" ]; then
        log "服务未能正常停止，正在强制终止..."
        echo "$remaining_pids" | while read pid; do
            kill -9 $pid 2>/dev/null || true
        done
        log "✅ 服务已强制终止"
    fi
}

# 重启服务
restart_service() {
    log "正在重启服务..."
    stop_service
    sleep 2
    start_service
}

# 显示服务状态
show_status() {
    log "服务状态:"
    if check_status; then
        local pid=$(get_pid)
        echo ""
        echo "📊 进程信息:"
        ps aux | grep "gunicorn.*$APP_NAME.*$PORT" | grep -v grep
        
        echo ""
        echo "🌐 端口监听:"
        netstat -tlnp 2>/dev/null | grep ":$PORT " || echo "端口 $PORT 未监听"
        
        echo ""
        echo "💾 资源使用:"
        if command -v htop > /dev/null 2>&1; then
            echo "使用 'htop -p $pid' 查看详细资源使用"
        else
            echo "使用 'top -p $pid' 查看详细资源使用"
        fi
    fi
}

# 显示日志
show_logs() {
    log "日志文件:"
    echo "📋 应用日志: $LOG_DIR/app.log"
    echo "❌ 错误日志: $LOG_DIR/error.log"
    echo "🌐 访问日志: $LOG_DIR/access.log"
    echo ""
    
    if [ -f "$LOG_DIR/app.log" ]; then
        echo "📋 最近的应用日志 (最后20行):"
        echo "----------------------------------------"
        tail -20 "$LOG_DIR/app.log"
        echo "----------------------------------------"
        echo ""
        echo "💡 使用 'tail -f $LOG_DIR/app.log' 实时查看日志"
    else
        echo "❌ 应用日志文件不存在"
    fi
    
    if [ -f "$LOG_DIR/error.log" ]; then
        echo ""
        echo "❌ 最近的错误日志 (最后10行):"
        echo "----------------------------------------"
        tail -10 "$LOG_DIR/error.log"
        echo "----------------------------------------"
    fi
}

# 显示帮助信息
show_help() {
    echo "生产环境管理脚本"
    echo ""
    echo "用法: $0 [命令]"
    echo ""
    echo "命令:"
    echo "  start    启动服务"
    echo "  stop     停止服务"
    echo "  restart  重启服务"
    echo "  status   查看服务状态"
    echo "  logs     查看日志"
    echo "  help     显示此帮助信息"
    echo ""
    echo "示例:"
    echo "  $0 start      # 启动服务"
    echo "  $0 stop       # 停止服务"
    echo "  $0 restart    # 重启服务"
    echo "  $0 status     # 查看状态"
    echo "  $0 logs       # 查看日志"
    echo ""
    echo "配置:"
    echo "  从 .env 文件读取配置，或使用默认值:"
    echo "  - PORT: $PORT"
    echo "  - WORKERS: $WORKERS"
    echo "  - LOG_DIR: $LOG_DIR"
}

# 主函数
main() {
    case "${1:-help}" in
        start)
            start_service
            ;;
        stop)
            stop_service
            ;;
        restart)
            restart_service
            ;;
        status)
            show_status
            ;;
        logs)
            show_logs
            ;;
        help|--help|-h)
            show_help
            ;;
        *)
            echo "❌ 未知命令: $1"
            echo ""
            show_help
            exit 1
            ;;
    esac
}

# 执行主函数
main "$@" 