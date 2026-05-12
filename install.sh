#!/bin/bash
set -e

WHL_URL="https://msstest.sankuai.com/ad-dqe-public/ai-coding-analysis/deep_ai_analysis-0.1.0-py3-none-any.whl"

echo "=================================================="
echo "  deep-ai-analysis 安装程序"
echo "=================================================="
echo ""

# Python 版本检测
PYTHON_BIN=$(command -v python3 || command -v python || echo "")
if [ -z "$PYTHON_BIN" ]; then
  echo "❌ 未找到 Python，请先安装 Python 3.10+"
  exit 1
fi
PYTHON_VERSION=$("$PYTHON_BIN" -c 'import sys; print(".".join(map(str, sys.version_info[:3])))')
echo "Python 版本：$PYTHON_VERSION  ($PYTHON_BIN)"

# 虚拟环境检测
if [ -n "$VIRTUAL_ENV" ]; then
  ENV_INFO="虚拟环境 (venv): $VIRTUAL_ENV"
elif [ -n "$CONDA_DEFAULT_ENV" ]; then
  ENV_INFO="Conda 环境: $CONDA_DEFAULT_ENV"
else
  ENV_INFO="系统 Python（未激活虚拟环境）"
fi
echo "当前环境：$ENV_INFO"

# pip 路径
PIP_BIN=$(command -v pip3 || command -v pip || echo "")
if [ -z "$PIP_BIN" ]; then
  echo "❌ 未找到 pip，请先安装 pip"
  exit 1
fi
echo "pip 路径：$PIP_BIN"

echo ""
echo "将安装 deep-ai-analysis 到上述环境。"
echo ""
read -p "确认继续安装？[y/N] " CONFIRM
case "$CONFIRM" in
  [yY][eE][sS]|[yY])
    ;;
  *)
    echo "已取消安装。"
    exit 0
    ;;
esac

echo ""
echo "正在安装..."
"$PIP_BIN" install "$WHL_URL"

echo ""
echo "✅ 安装完成！运行 'deep-ai-analysis --help' 查看使用说明。"
