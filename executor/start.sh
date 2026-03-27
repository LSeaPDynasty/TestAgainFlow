#!/bin/bash

echo "╔═══════════════════════════════════════════════════════════╗"
echo "║                                                           ║"
echo "║        🤖 TestFlow Execution Engine v1.0.0                ║"
echo "║                                                           ║"
echo "║        Android 自动化测试执行引擎                          ║"
echo "║                                                           ║"
echo "╚═══════════════════════════════════════════════════════════╝"
echo ""

# 检查Python
if ! command -v python3 &> /dev/null; then
    echo "❌ 错误: 未找到Python，请先安装Python 3.9+"
    exit 1
fi

# 检查虚拟环境
if [ ! -d "venv" ]; then
    echo "📦 创建虚拟环境..."
    python3 -m venv venv
fi

# 激活虚拟环境
echo "🔧 激活虚拟环境..."
source venv/bin/activate

# 安装依赖
echo "📥 检查依赖..."
pip install -q -r requirements.txt

# 启动执行引擎
echo ""
echo "▶️  启动执行引擎..."
echo ""
python main.py
