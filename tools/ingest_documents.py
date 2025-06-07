import os
import sys
import shutil
import time
import gc

# 将项目根目录添加到Python路径
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(project_root)

from src.agents.rag_agent import RAGAgent

def force_cleanup_database(db_dir):
    """强制清理数据库文件，处理文件锁定问题"""
    if not os.path.exists(db_dir):
        return

    print(f"正在清理数据库目录: {db_dir}")

    # 尝试多次删除，处理文件锁定问题
    max_attempts = 5
    for attempt in range(max_attempts):
        try:
            if os.path.isdir(db_dir):
                shutil.rmtree(db_dir)
            else:
                os.remove(db_dir)
            print(f"成功删除数据库目录: {db_dir}")
            break
        except PermissionError as e:
            print(f"尝试 {attempt + 1}/{max_attempts}: 文件被占用，等待释放...")
            if attempt < max_attempts - 1:
                time.sleep(2)  # 等待2秒后重试
                gc.collect()  # 强制垃圾回收
            else:
                print(f"警告: 无法删除 {db_dir}，可能被其他进程占用")
                print("请手动关闭相关进程或重启程序")
                # 尝试重命名而不是删除
                try:
                    backup_name = f"{db_dir}_backup_{int(time.time())}"
                    os.rename(db_dir, backup_name)
                    print(f"已将旧数据库重命名为: {backup_name}")
                except Exception as rename_error:
                    print(f"重命名也失败: {rename_error}")
                    raise e
        except Exception as e:
            print(f"删除数据库时出错: {e}")
            if attempt == max_attempts - 1:
                raise

def main():
    print("=== RAG知识库文档导入工具 ===")
    
    # 检查docs目录是否有文件
    docs_dir = "docs"
    if not os.path.exists(docs_dir):
        os.makedirs(docs_dir)
        print(f"已创建{docs_dir}目录，请将文档放入该目录")
        return
    
    # 检查文件数量
    pdf_files = [f for f in os.listdir(docs_dir) if f.endswith('.pdf')]
    docx_files = [f for f in os.listdir(docs_dir) if f.endswith('.docx') or f.endswith('.doc')]
    txt_files = [f for f in os.listdir(docs_dir) if f.endswith('.txt')]

    print(f"pdf_files: {pdf_files}")
    print(f"docx_files: {docx_files}")
    print(f"txt_files: {txt_files}")
    
    total_files = len(pdf_files) + len(docx_files) + len(txt_files)
    
    if total_files == 0:
        print(f"错误: {docs_dir}目录中没有找到任何支持的文档(PDF/DOCX/TXT)")
        print("请添加文档后再运行此脚本")
        return
    
    print(f"发现以下文档:")
    print(f"- PDF文件: {len(pdf_files)}个")
    print(f"- Word文件: {len(docx_files)}个")
    print(f"- 文本文件: {len(txt_files)}个")
    
    # 确认是否重新创建知识库
    # response = input("是否重新构建知识库？这将删除现有的向量数据库 (y/n): ")
    
    # if response.lower() == 'y':
    # 使用与use_custom_api.py一致的数据库目录名
    db_dir = "vector_db"
    
    # 强制清理现有向量库
    force_cleanup_database(db_dir)

    # 检查是否存在旧的db文件或目录并处理
    old_db = "db"
    if os.path.exists(old_db):
        force_cleanup_database(old_db)

    # 强制垃圾回收，释放可能的资源
    gc.collect()
    time.sleep(1)  # 给系统一点时间释放资源

    # 创建RAG代理并处理文档
    print("开始构建新知识库...")
    try:
        agent = RAGAgent(docs_dir=docs_dir, persist_dir=db_dir,api_base="https://api.ai-gaochao.cn/v1",api_key="sk-LJnOebUUtdz3fZ5V2a3eD48a810c41BfBe7000183bCa0cCf")
        print("知识库构建完成!")
        agent.cleanup()
        del agent
        gc.collect()

    except Exception as e:
        print(f"构建知识库时出错: {e}")
        raise

if __name__ == "__main__":
    main()
