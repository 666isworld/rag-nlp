"""
RAG知识库系统管理工具 - 主入口脚本
"""
import os
import sys
import subprocess

def execute_script(script_path, description):
    """执行指定的Python脚本"""
    print(f"\n正在{description}...")
    try:
        result = subprocess.run([sys.executable, script_path], check=True)
        return result.returncode == 0
    except subprocess.CalledProcessError as e:
        print(f"执行出错: {str(e)}")
        return False

def main():
    """主函数"""

    execute_script("simple_gui_pyside.py", "启动图形化界面")

if __name__ == "__main__":
    main()
