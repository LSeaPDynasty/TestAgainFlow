"""
启动执行引擎Web GUI界面
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

    print("启动 TestFlow 执行引擎 Web GUI...")
    print("=" * 60)
    print("Web界面地址: http://127.0.0.1:5000")
    print("按 Ctrl+C 停止服务器")
    print("=" * 60)

    # 切换到gui目录
    gui_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'gui')
    os.chdir(gui_dir)

    # 延迟3秒打开浏览器
    Timer(3, open_browser).start()

    # 启动Flask服务器
    try:
        from gui.web_server import main as web_main
        web_main()
    except ImportError:
        # 如果导入失败，直接运行web_server.py
        subprocess.run([sys.executable, 'web_server.py'])

if __name__ == '__main__':
    main()