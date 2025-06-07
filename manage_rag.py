"""
RAG知识库系统管理工具 - 主入口脚本
"""
import os
import sys
import subprocess

def show_header():
    """显示程序标题"""
    print("="*60)
    print("  RAG知识库系统管理工具")
    print("="*60)

def show_menu():
    """显示菜单选项"""
    print("\n请选择要执行的操作:")
    # print("1. 设置环境（安装依赖包）")
    print("1. 创建知识库目录结构")
    print("2. 下载模型（需要VPN）")
    print("3. 导入文档到知识库")
    print("4. 更新RAG代理使用本地模型")
    print("5. 启动问答系统（命令行）")
    print("6. 启动图形化界面")
    # print("8. 修复所有警告和错误")
    # print("9. 修复NumPy兼容性问题")
    # print("10. 使用全新修复版RAG代理")
    print("0. 退出")
    
    choice = input("\n请输入选项编号 [0-6]: ")
    return choice

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
    show_header()
    
    while True:
        choice = show_menu()
        
        # if choice == "1":
        #     execute_script("tools/setup_environment.py", "设置环境")
        if choice == "1":
            execute_script("tools/setup_knowledge_base.py", "创建知识库目录结构")
        elif choice == "2":
            execute_script("tools/download_models.py", "下载模型")
        elif choice == "3":
            execute_script("tools/ingest_documents.py", "导入文档")
        elif choice == "4":
            execute_script("tools/update_with_local_models.py", "更新使用本地模型")
        elif choice == "5":
            execute_script("rag_app.py", "启动命令行问答系统")
        elif choice == "6":
            execute_script("simple_gui_pyside.py", "启动原生Tk图形界面")
        # elif choice == "8":
        #     execute_script("tools/fix_all_warnings.py", "修复所有警告和错误")
        # elif choice == "9":
        #     execute_script("tools/fix_numpy_compatibility.py", "修复NumPy兼容性问题")
        # elif choice == "10":
        #     execute_script("tools/use_fixed_agent.py", "应用全新修复版RAG代理")
        elif choice == "0":
            print("\n谢谢使用，再见！")
            break
        else:
            print("\n无效选项，请重新输入。")
        
        input("\n按Enter键继续...")

if __name__ == "__main__":
    main()
