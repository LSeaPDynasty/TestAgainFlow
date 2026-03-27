"""
启动执行引擎WebSocket GUI界面
"""
import os
import sys
import subprocess
import webbrowser
from threading import Timer

def open_browser():
    """延迟打开浏览器"""
    webbrowser.open('http://127.0.0.1:5000')

def main():
    """主函数"""
    import sys
    if sys.platform == 'win32':
        import codecs
        sys.stdout.reconfigure(encoding='utf-8', errors='replace')

    print("启动 TestFlow 执行引擎 WebSocket GUI...")
    print("=" * 60)
    print("Web界面地址: http://127.0.0.1:5000")
    print("后端WebSocket: ws://localhost:8000")
    print("按 Ctrl+C 停止服务器")
    print("=" * 60)

    # 切换到executor目录
    executor_dir = os.path.dirname(os.path.abspath(__file__))
    os.chdir(executor_dir)

    # 延迟3秒打开浏览器
    Timer(3, open_browser).start()

    # 启动WebSocket GUI服务器
    try:
        from gui.web_server_ws import main as ws_main
        import argparse

        parser = argparse.ArgumentParser(description='TestFlow Executor WebSocket GUI')
        parser.add_argument('--backend-url', default='ws://localhost:8000',
                           help='后端WebSocket服务器URL')
        parser.add_argument('--host', default='127.0.0.1', help='Web服务器主机')
        parser.add_argument('--port', type=int, default=5000, help='Web服务器端口')

        args = parser.parse_args()

        # 导入并启动服务器
        from gui.web_server_ws import ExecutorWebServerWS
        server = ExecutorWebServerWS(backend_url=args.backend_url)
        server.start(host=args.host, port=args.port, debug=False)

    except ImportError as e:
        print(f"导入失败: {e}")
        print("请确保已安装所有依赖: pip install websockets")
        sys.exit(1)
    except KeyboardInterrupt:
        print("\n停止服务器...")
        sys.exit(0)

if __name__ == '__main__':
    main()