import os
import sys
import time

from src.agents.rag_agent import RAGAgent

# 兼容性修复：为Python 3.10添加typing.Self支持
try:
    from typing import Self
except ImportError:
    try:
        from typing_extensions import Self
    except ImportError:
        # 如果都没有，创建一个占位符
        Self = None
from PySide6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QLabel, QTextEdit, QPushButton, QSplitter, QStatusBar,
    QMessageBox, QGroupBox, QProgressBar, QFileDialog, QDialog,
    QListWidget, QDialogButtonBox, QListWidgetItem, QFrame, QComboBox
)
from PySide6.QtCore import Qt, QThread, Signal, QSize
from PySide6.QtGui import QFont, QIcon
import gc,shutil

class RAGAgentFactory:
    def __init__(self):
        self.__agent = None
    
    def set_agent(self,agent):
        print(f"设置前的agent: {self.__agent}")
        if self.__agent is not None:
            self.__agent.cleanup()
            del self.__agent
        self.__agent = agent
        print(f"设置后的agent: {self.__agent}")
    
    def get_agent(self):
        return self.__agent
    
    def create_agent(self,docs_dir="docs",db_dir="vector_db",model_name="all-MiniLM-L6-v2"):
        if self.__agent is None:
            self.__agent = RAGAgent(
                docs_dir=docs_dir,
                persist_dir=db_dir,
                api_base="https://api.ai-gaochao.cn/v1",
                api_key="sk-LJnOebUUtdz3fZ5V2a3eD48a810c41BfBe7000183bCa0cCf",
                model_name=model_name
                )
        return self.__agent


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


class SheetSelectionDialog(QDialog):
    """工作表选择对话框"""
    def __init__(self, sheet_names, parent=None):
        super().__init__(parent)
        self.setWindowTitle("选择工作表")
        self.setModal(True)
        self.resize(300, 200)

        layout = QVBoxLayout(self)

        # 说明标签
        label = QLabel("请选择要处理的工作表:")
        layout.addWidget(label)

        # 工作表列表
        self.sheet_list = QListWidget()
        self.sheet_list.addItems(sheet_names)
        if sheet_names:
            self.sheet_list.setCurrentRow(0)  # 默认选择第一个
        layout.addWidget(self.sheet_list)

        # 按钮
        button_box = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        button_box.accepted.connect(self.accept)
        button_box.rejected.connect(self.reject)
        layout.addWidget(button_box)

    def get_selected_sheet(self):
        """获取选中的工作表名称"""
        current_item = self.sheet_list.currentItem()
        return current_item.text() if current_item else None


class DocumentManagerDialog(QDialog):
    """文档管理对话框"""
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("知识库文档管理")
        self.setModal(True)
        self.resize(600, 500)
        self.parent_window = parent

        # 创建布局
        layout = QVBoxLayout(self)

        # 标题
        title_label = QLabel("当前知识库文档")
        title_label.setStyleSheet("font-size: 14px; font-weight: bold; margin: 10px 0;")
        layout.addWidget(title_label)

        # 文档列表
        self.doc_list = QListWidget()
        self.doc_list.setStyleSheet("""
            QListWidget {
                border: 1px solid #ddd;
                border-radius: 6px;
                background-color: #fafafa;
                padding: 5px;
            }
            QListWidget::item {
                padding: 8px;
                border-bottom: 1px solid #eee;
                border-radius: 4px;
                margin: 2px;
            }
            QListWidget::item:selected {
                background-color: #e3f2fd;
                color: #1976d2;
            }
            QListWidget::item:hover {
                background-color: #f5f5f5;
            }
        """)
        layout.addWidget(self.doc_list)

        # 状态标签
        self.status_label = QLabel("正在加载文档列表...")
        self.status_label.setStyleSheet("color: #666; font-size: 10px; margin: 5px 0;")
        layout.addWidget(self.status_label)

        # 按钮区域
        button_layout = QHBoxLayout()

        self.upload_btn = QPushButton("上传文档")
        self.upload_btn.setStyleSheet("background-color: #2196F3; color: white; padding: 8px 16px; border-radius: 4px;")
        self.upload_btn.clicked.connect(self.upload_documents)
        button_layout.addWidget(self.upload_btn)

        self.update_btn = QPushButton("更新知识库")
        self.update_btn.setStyleSheet("background-color: #FF9800; color: white; padding: 8px 16px; border-radius: 4px;")
        self.update_btn.clicked.connect(self.update_knowledge_base)
        button_layout.addWidget(self.update_btn)

        button_layout.addStretch()

        self.close_btn = QPushButton("返回")
        self.close_btn.setStyleSheet("background-color: #757575; color: white; padding: 8px 16px; border-radius: 4px;")
        self.close_btn.clicked.connect(self.close)
        button_layout.addWidget(self.close_btn)

        layout.addLayout(button_layout)

        # 加载文档列表
        self.load_documents()

    def load_documents(self):
        """加载文档列表"""
        try:
            docs_dir = "docs"
            if not os.path.exists(docs_dir):
                self.status_label.setText("docs目录不存在")
                return

            # 获取所有支持的文档文件
            supported_extensions = ['.pdf', '.doc', '.docx', '.txt','.md']
            documents = []

            for root, dirs, files in os.walk(docs_dir):
                for file in files:
                    if any(file.lower().endswith(ext) for ext in supported_extensions):
                        file_path = os.path.join(root, file)
                        rel_path = os.path.relpath(file_path, docs_dir)
                        file_size = os.path.getsize(file_path)
                        documents.append((rel_path, file_size))

            # 清空列表
            self.doc_list.clear()

            if not documents:
                self.status_label.setText("没有找到任何文档文件")
                return

            # 添加文档到列表
            for doc_path, file_size in documents:
                size_str = self.format_file_size(file_size)
                item_text = f"{doc_path} ({size_str})"

                item = QListWidgetItem(item_text)
                item.setToolTip(f"文件路径: {doc_path}\n文件大小: {size_str}")
                self.doc_list.addItem(item)

            self.status_label.setText(f"共找到 {len(documents)} 个文档文件")

        except Exception as e:
            self.status_label.setText(f"加载文档列表出错: {str(e)}")

    def format_file_size(self, size_bytes):
        """格式化文件大小"""
        if size_bytes < 1024:
            return f"{size_bytes} B"
        elif size_bytes < 1024 * 1024:
            return f"{size_bytes / 1024:.1f} KB"
        else:
            return f"{size_bytes / (1024 * 1024):.1f} MB"

    def upload_documents(self):
        """上传文档"""

        file_paths, _ = QFileDialog.getOpenFileNames(
            self,
            "选择要上传的文档",
            "",
            "文档文件 (*.pdf *.doc *.docx *.txt);;PDF文件 (*.pdf);;Word文档 (*.doc *.docx);;文本文件 (*.txt)"
        )

        if not file_paths:
            return

        try:
            docs_dir = "docs"
            if not os.path.exists(docs_dir):
                os.makedirs(docs_dir)

            uploaded_count = 0
            for file_path in file_paths:
                filename = os.path.basename(file_path)
                dest_path = os.path.join(docs_dir, filename)

                # 如果文件已存在，询问是否覆盖
                if os.path.exists(dest_path):
                    reply = QMessageBox.question(
                        self,
                        "文件已存在",
                        f"文件 '{filename}' 已存在，是否覆盖？",
                        QMessageBox.Yes | QMessageBox.No,
                        QMessageBox.No
                    )
                    if reply != QMessageBox.Yes:
                        continue

                # 复制文件
                import shutil
                shutil.copy2(file_path, dest_path)
                uploaded_count += 1

            if uploaded_count > 0:
                QMessageBox.information(self, "上传成功", f"成功上传 {uploaded_count} 个文件")
                self.load_documents()  # 重新加载文档列表

        except Exception as e:
            QMessageBox.critical(self, "上传失败", f"上传文档时出错: {str(e)}")

    def update_knowledge_base(self):
        """更新知识库"""
        reply = QMessageBox.question(
            self,
            "确认更新",
            "确定要更新知识库吗？这可能需要一些时间。",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No
        )

        if reply == QMessageBox.Yes:
            # 通知父窗口开始更新知识库
            if self.parent_window:
                self.parent_window.start_knowledge_base_update()
            self.close()


class BatchProcessWorker(QThread):
    """批量处理工作线程"""
    progress_update = Signal(int, int, str)  # 当前进度, 总数, 当前问题
    finished = Signal(str)  # 输出文件路径
    error = Signal(str)  # 错误消息

    def __init__(self, agent, file_path, sheet_name, output_path):
        super().__init__()
        self.agent = agent
        self.file_path = file_path
        self.sheet_name = sheet_name
        self.output_path = output_path

    def run(self):
        try:
            import pandas as pd

            # 读取Excel文件
            df = pd.read_excel(self.file_path, sheet_name=self.sheet_name)

            if df.empty:
                self.error.emit("Excel文件为空或无法读取")
                return

            # 获取第一列的问题
            questions = df.iloc[:, 0].dropna().astype(str).tolist()

            if not questions:
                self.error.emit("第一列没有找到有效的问题")
                return

            # 确保有第二列用于存放答案
            if len(df.columns) < 2:
                df['答案'] = ''

            total_questions = len(questions)
            answers = []

            # 逐个处理问题
            for i, question in enumerate(questions):
                if not question.strip():
                    answers.append("")
                    continue

                self.progress_update.emit(i + 1, total_questions, question)

                try:
                    # 查询答案
                    answer = self.agent.query(question.strip())
                    answers.append(answer)
                except Exception as e:
                    error_msg = f"查询出错: {str(e)}"
                    answers.append(error_msg)

            # 将答案写入第二列
            df.iloc[:len(answers), 1] = answers

            # 保存结果
            df.to_excel(self.output_path, index=False)

            self.finished.emit(self.output_path)

        except Exception as e:
            self.error.emit(f"批量处理出错: {str(e)}")


class UpdateKnowledgeBaseWorker(QThread):
    """更新知识库工作线程"""
    finished = Signal(str)  # 完成消息
    error = Signal(str)  # 错误消息
    output_update = Signal(str)  # 输出更新

    def __init__(self, parent, model_name):
        super().__init__()
        self.parent_window = parent
        self.model_name = model_name

    def run(self):
        try:
            import gc
            from src.agents.rag_agent import RAGAgent
            docs_dir,db_dir = "docs","vector_db"
            self.parent_window.close_all_workers()
            self.parent_window.rag_agent_factory.set_agent(None)
            # 强制清理现有向量库
            force_cleanup_database(db_dir)
            # 创建RAG代理并处理文档
            print("开始构建新知识库...")
            self.parent_window.rag_agent_factory.create_agent(model_name=self.model_name)
            print("知识库构建完成!")
            self.finished.emit("知识库更新完成！")
        except Exception as e:
            self.error.emit(f"更新知识库出错: {str(e)}")


class InitializeWorker(QThread):
    """初始化工作线程"""
    finished = Signal(str)  # agent对象, 状态消息
    error = Signal(str)  # 错误消息
    status_update = Signal(str)  # 状态更新

    def __init__(self, parent, model_name):
        super().__init__()
        self.parent_window = parent
        self.model_name = model_name

    def run(self):
        # try:

            self.parent_window.rag_agent_factory.create_agent(model_name=self.model_name)

            self.finished.emit("知识库已成功加载！")
        # except Exception as e:
        #     error_msg = f"初始化出错: {str(e)}"
        #     self.error.emit(error_msg)


class QueryWorker(QThread):
    """查询工作线程"""
    finished = Signal(str, float)  # 回答, 耗时
    error = Signal(str)  # 错误消息

    def __init__(self, agent, question):
        super().__init__()
        self.agent = agent
        self.question = question

    def run(self):
        try:
            start_time = time.time()
            response = self.agent.query(self.question)
            end_time = time.time()
            query_time = end_time - start_time
            self.finished.emit(response, query_time)
        except Exception as e:
            self.error.emit(f"查询出错: {str(e)}")


class SimpleRAGTkApp(QMainWindow):
    def __init__(self):
        """初始化应用"""
        super().__init__()
        self.status = "未初始化"
        self.init_worker = None
        self.query_worker = None
        self.batch_worker = None
        self.update_kb_worker = None
        self.model_name = "all-MiniLM-L6-v2"
        self.rag_agent_factory = RAGAgentFactory()
        
        self.setWindowTitle("面向多学科学习的RAG智能助手")
        self.setGeometry(100, 100, 1000, 700)
        self.setMinimumSize(800, 600)
        
        # 设置应用样式
        self.setup_style()
        
        # 创建中央部件
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        # 创建主布局
        self.main_layout = QVBoxLayout(central_widget)
        self.main_layout.setSpacing(10)
        self.main_layout.setContentsMargins(15, 15, 15, 15)
        
        self.create_widgets()

        # 创建状态栏
        self.status_bar = QStatusBar()
        self.setStatusBar(self.status_bar)
        self.status_bar.showMessage("准备就绪")

        self.update_status("就绪，请初始化知识库", "#2196F3")
    
    def setup_style(self):
        """设置应用样式"""
        self.setStyleSheet("""
            QMainWindow {
                background-color: #f5f5f5;
            }
            QGroupBox {
                font-weight: bold;
                border: 2px solid #cccccc;
                border-radius: 8px;
                margin-top: 1ex;
                padding-top: 10px;
                background-color: white;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 10px;
                padding: 0 5px 0 5px;
                color: #333333;
            }
            QPushButton {
                border: none;
                border-radius: 6px;
                padding: 8px 16px;
                font-weight: bold;
                font-size: 11px;
            }
            QPushButton:hover {
                opacity: 0.8;
            }
            QPushButton:pressed {
                opacity: 0.6;
            }
            QTextEdit {
                border: 1px solid #ddd;
                border-radius: 6px;
                padding: 8px;
                background-color: white;
                font-family: 'Segoe UI', Arial, sans-serif;
            }
            QLabel {
                color: #333333;
            }
        """)
    
    def create_widgets(self):
        """创建GUI组件"""
        # 标题区域
        title_label = QLabel("面向多学科学习的RAG智能助手")
        title_label.setAlignment(Qt.AlignCenter)
        title_font = QFont("Microsoft YaHei", 18, QFont.Bold)
        title_label.setFont(title_font)
        title_label.setStyleSheet("color: #1976D2; margin: 10px 0;")
        self.main_layout.addWidget(title_label)
        
        # 状态显示区域
        status_group = QGroupBox("系统状态")
        status_layout = QHBoxLayout(status_group)
        
        self.status_label = QLabel(self.status)
        self.status_label.setStyleSheet("color: #2196F3; font-weight: bold; padding: 5px;")
        status_layout.addWidget(self.status_label)
        
        self.model_combo = QComboBox()
        self.model_combo.addItem("all-MiniLM-L6-v2（通用）")
        # self.model_combo.addItem("distiluse-base-multilingual-cased-v1")
        # self.model_combo.addItem("bert-base-chinese")
        self.model_combo.currentTextChanged.connect(self.on_model_changed)
        self.model_combo.setStyleSheet("""
            QComboBox {
                border: 1px solid #ddd;
                border-radius: 4px;
                padding: 4px;
                background: white;
            }
            QComboBox::drop-down {
                border: none;
                width: 20px;
            }
        """)
        status_layout.addWidget(self.model_combo)
        
        # 进度条
        self.progress_bar = QProgressBar()
        self.progress_bar.setVisible(False)
        self.progress_bar.setStyleSheet("""
            QProgressBar {
                border: 1px solid #ddd;
                border-radius: 4px;
                text-align: center;
            }
            QProgressBar::chunk {
                background-color: #4CAF50;
                border-radius: 3px;
            }
        """)
        status_layout.addWidget(self.progress_bar)
        
        self.main_layout.addWidget(status_group)
        
        # 创建分割器
        splitter = QSplitter(Qt.Vertical)
        
        # 聊天区域
        chat_group = QGroupBox("对话区域")
        chat_layout = QVBoxLayout(chat_group)
        
        # 聊天历史
        self.chat_history = QTextEdit()
        self.chat_history.setReadOnly(True)
        # self.chat_history.setMinimumHeight(300)
        chat_font = QFont("Microsoft YaHei", 10)
        self.chat_history.setFont(chat_font)
        self.chat_history.setStyleSheet("""
            QTextEdit {
                background-color: #fafafa;
                border: 1px solid #e0e0e0;
            }
        """)
        chat_layout.addWidget(self.chat_history)
        
        splitter.addWidget(chat_group)
        
        # 输入区域
        input_group = QGroupBox("问题输入")
        input_layout = QVBoxLayout(input_group)
        
        self.question_input = QTextEdit()
        self.question_input.setMaximumHeight(100)
        self.question_input.setPlaceholderText("请在此输入您的问题...")
        input_layout.addWidget(self.question_input)
        
        # 按钮和时间显示
        button_layout = QHBoxLayout()
        
        self.send_btn = QPushButton("发送问题")
        self.send_btn.setStyleSheet("background-color: #2196F3; color: white;")
        self.send_btn.clicked.connect(self.send_question)
        button_layout.addWidget(self.send_btn)
        
        self.clear_btn = QPushButton("清空对话")
        self.clear_btn.setStyleSheet("background-color: #757575; color: white;")
        self.clear_btn.clicked.connect(self.clear_chat)
        button_layout.addWidget(self.clear_btn)
        
        button_layout.addStretch()
        
        self.time_label = QLabel("")
        self.time_label.setStyleSheet("color: #666; font-size: 10px;")
        button_layout.addWidget(self.time_label)
        
        input_layout.addLayout(button_layout)
        splitter.addWidget(input_group)
        
        # 设置分割器比例
        splitter.setSizes([400, 300])
        self.main_layout.addWidget(splitter)
        
        # 操作按钮区域
        ops_group = QGroupBox("操作")
        ops_layout = QHBoxLayout(ops_group)
        
        self.init_btn = QPushButton("初始化知识库")
        self.init_btn.setStyleSheet("background-color: #4CAF50; color: white;")
        self.init_btn.clicked.connect(self.initialize_agent)
        ops_layout.addWidget(self.init_btn)

        self.batch_btn = QPushButton("批量导入")
        self.batch_btn.setStyleSheet("background-color: #9C27B0; color: white;")
        self.batch_btn.clicked.connect(self.batch_import)
        ops_layout.addWidget(self.batch_btn)

        self.docs_btn = QPushButton("查看知识库")
        self.docs_btn.setStyleSheet("background-color: #607D8B; color: white;")
        self.docs_btn.clicked.connect(self.view_knowledge_base)
        ops_layout.addWidget(self.docs_btn)

        ops_layout.addStretch()

        self.exit_btn = QPushButton("退出")
        self.exit_btn.setStyleSheet("background-color: #F44336; color: white;")
        self.exit_btn.clicked.connect(self.close)
        ops_layout.addWidget(self.exit_btn)
        
        self.main_layout.addWidget(ops_group)
        
        # 使用说明
        help_text = "使用说明: 点击'初始化知识库'按钮加载知识库，然后在问题框中输入问题，点击'发送问题'获取回答。支持Ctrl+Enter快捷键发送。点击'批量导入'可以上传Excel文件进行批量问答处理。点击'查看知识库'可以管理文档和更新知识库。"
        help_label = QLabel(help_text)
        help_label.setWordWrap(True)
        help_label.setStyleSheet("color: #666; font-size: 9px; margin: 5px 0;")
        self.main_layout.addWidget(help_label)
        
        # 绑定快捷键
        self.question_input.installEventFilter(self)

    def eventFilter(self, obj, event):
        """事件过滤器，处理快捷键"""
        if obj == self.question_input:
            if event.type() == event.Type.KeyPress:
                if event.key() == Qt.Key_Return and event.modifiers() == Qt.ControlModifier:
                    self.send_question()
                    return True
        return super().eventFilter(obj, event)

    def update_status(self, status_msg, color="#2196F3"):
        """更新状态消息"""
        self.status = status_msg
        self.status_label.setText(status_msg)
        self.status_label.setStyleSheet(f"color: {color}; font-weight: bold; padding: 5px;")
        self.status_bar.showMessage(status_msg)

    def append_to_chat(self, text, is_user=False):
        """添加消息到聊天历史"""
        if self.chat_history.toPlainText():
            self.chat_history.append("")

        prefix = "🙋 您: " if is_user else "🤖 系统: "

        # 设置不同的颜色样式
        if is_user:
            self.chat_history.append(f'<div style="color: #1976D2; font-weight: bold; margin: 5px 0;">{prefix}{text}</div>')
            # self.chat_history.append(f'<div style="margin-left: 20px; margin-bottom: 10px;">{text}</div>')
        else:
            self.chat_history.append(f'<div style="color: #388E3C; font-weight: bold; margin: 5px 0;">{prefix}{text}</div>')
            # self.chat_history.append(f'<div style="margin-left: 20px; margin-bottom: 10px; background-color: #f8f9fa; padding: 8px; border-radius: 4px;">{text}</div>')

        # 滚动到底部
        scrollbar = self.chat_history.verticalScrollBar()
        scrollbar.setValue(scrollbar.maximum())

    def show_progress(self, show=True):
        """显示或隐藏进度条"""
        self.progress_bar.setVisible(show)
        if show:
            self.progress_bar.setRange(0, 0)  # 无限进度条

    def initialize_agent(self):
        """初始化RAG代理"""
        self.update_status("正在初始化知识库...", "#FF9800")
        self.show_progress(True)
        self.init_btn.setEnabled(False)
        
        self.update_status(f"正在使用模型 {self.model_name} 初始化...", "#FF9800")

        # 清理之前的线程
        if self.init_worker is not None:
            self.init_worker.quit()
            self.init_worker.wait()

        # 创建新的工作线程
        self.init_worker = InitializeWorker(self,model_name=self.model_name)
        self.init_worker.finished.connect(self._on_initialize_finished)
        self.init_worker.error.connect(self._on_initialize_error)
        self.init_worker.status_update.connect(lambda msg: self.update_status(msg, "#FF9800"))
        self.init_worker.start()

    def _on_initialize_finished(self, message):
        """初始化成功回调"""
        self.show_progress(False)
        self.init_btn.setEnabled(True)
        self.update_status(message, "#4CAF50")

        # 清理线程
        if self.init_worker:
            self.init_worker.deleteLater()
            self.init_worker = None

    def _on_initialize_error(self, error_msg):
        """初始化错误回调"""
        self.show_progress(False)
        self.init_btn.setEnabled(True)
        self.update_status(error_msg, "#F44336")
        QMessageBox.critical(self, "初始化错误", error_msg)

        # 清理线程
        if self.init_worker:
            self.init_worker.deleteLater()
            self.init_worker = None

    def send_question(self):
        """发送问题并获取回答"""
        question = self.question_input.toPlainText().strip()
        if not question:
            return

        if not self.rag_agent_factory.get_agent():
            self.append_to_chat("请先初始化知识库！")
            self.update_status("请先初始化知识库", "#F44336")
            return

        # 清空输入框
        self.question_input.clear()
        self.append_to_chat(question, is_user=True)

        # 更新状态
        self.update_status("正在查询知识库...", "#2196F3")
        self.show_progress(True)
        self.send_btn.setEnabled(False)

        # 清理之前的查询线程
        if self.query_worker is not None:
            self.query_worker.quit()
            self.query_worker.wait()

        # 创建查询线程

        print(f"查询的agent: {self.rag_agent_factory.get_agent().qa_chain}")
        self.query_worker = QueryWorker(self.rag_agent_factory.get_agent(), question)
        self.query_worker.finished.connect(self._on_query_finished)
        self.query_worker.error.connect(self._on_query_error)
        self.query_worker.start()

    def _on_query_finished(self, response, query_time):
        """查询成功回调"""
        self.show_progress(False)
        self.send_btn.setEnabled(True)

        # 更新界面
        self.append_to_chat(response)
        self.time_label.setText(f"查询用时: {query_time:.2f}秒")
        self.update_status("就绪", "#4CAF50")

        # 清理线程
        if self.query_worker:
            self.query_worker.deleteLater()
            self.query_worker = None

    def _on_query_error(self, error_msg):
        """查询错误回调"""
        self.show_progress(False)
        self.send_btn.setEnabled(True)

        self.append_to_chat(error_msg)
        self.update_status(error_msg, "#F44336")

        # 清理线程
        if self.query_worker:
            self.query_worker.deleteLater()
            self.query_worker = None

    def clear_chat(self):
        """清空聊天历史"""
        self.chat_history.clear()
        self.time_label.clear()

    def batch_import(self):
        """批量导入Excel文件进行处理"""
        if not self.rag_agent_factory.get_agent():
            QMessageBox.warning(self, "警告", "请先初始化知识库！")
            return

        # 选择Excel文件
        file_path, _ = QFileDialog.getOpenFileName(
            self,
            "选择Excel文件",
            "",
            "Excel文件 (*.xlsx *.xls)"
        )

        if not file_path:
            return

        try:
            import pandas as pd

            # 读取Excel文件获取工作表名称
            excel_file = pd.ExcelFile(file_path)
            sheet_names = excel_file.sheet_names

            if not sheet_names:
                QMessageBox.critical(self, "错误", "Excel文件中没有找到工作表")
                return

            # 让用户选择工作表
            dialog = SheetSelectionDialog(sheet_names, self)
            if dialog.exec() != QDialog.Accepted:
                return

            selected_sheet = dialog.get_selected_sheet()
            if not selected_sheet:
                QMessageBox.critical(self, "错误", "请选择一个工作表")
                return

            # 选择输出文件路径
            output_path, _ = QFileDialog.getSaveFileName(
                self,
                "保存结果文件",
                f"{os.path.splitext(os.path.basename(file_path))[0]}_结果.xlsx",
                "Excel文件 (*.xlsx)"
            )

            if not output_path:
                return

            # 开始批量处理
            self.start_batch_processing(file_path, selected_sheet, output_path)

        except ImportError:
            QMessageBox.critical(self, "错误", "缺少pandas库，请安装: pip install pandas openpyxl")
        except Exception as e:
            QMessageBox.critical(self, "错误", f"读取Excel文件出错: {str(e)}")

    def start_batch_processing(self, file_path, sheet_name, output_path):
        """开始批量处理"""
        self.update_status("正在进行批量处理...", "#9C27B0")
        self.show_progress(True)
        self.batch_btn.setEnabled(False)

        # 清理之前的批量处理线程
        if self.batch_worker is not None:
            self.batch_worker.quit()
            self.batch_worker.wait()

        # 创建批量处理线程
        self.batch_worker = BatchProcessWorker(self.rag_agent_factory.get_agent(), file_path, sheet_name, output_path)
        self.batch_worker.progress_update.connect(self._on_batch_progress)
        self.batch_worker.finished.connect(self._on_batch_finished)
        self.batch_worker.error.connect(self._on_batch_error)
        self.batch_worker.start()

    def _on_batch_progress(self, current, total, question):
        """批量处理进度更新"""
        self.progress_bar.setRange(0, total)
        self.progress_bar.setValue(current)
        self.update_status(f"正在处理 {current}/{total}: {question[:50]}...", "#9C27B0")

    def _on_batch_finished(self, output_path):
        """批量处理完成"""
        self.show_progress(False)
        self.batch_btn.setEnabled(True)
        self.update_status("批量处理完成！", "#4CAF50")

        # 显示完成消息
        msg = QMessageBox(self)
        msg.setWindowTitle("批量处理完成")
        msg.setText(f"批量处理已完成！\n结果已保存到: {output_path}")
        msg.setStandardButtons(QMessageBox.Ok)
        msg.setDefaultButton(QMessageBox.Ok)

        # 清理线程
        if self.batch_worker:
            self.batch_worker.deleteLater()
            self.batch_worker = None

    def _on_batch_error(self, error_msg):
        """批量处理错误"""
        self.show_progress(False)
        self.batch_btn.setEnabled(True)
        self.update_status(error_msg, "#F44336")
        QMessageBox.critical(self, "批量处理错误", error_msg)

        # 清理线程
        if self.batch_worker:
            self.batch_worker.deleteLater()
            self.batch_worker = None

    def view_knowledge_base(self):
        """查看知识库文档"""
        dialog = DocumentManagerDialog(self)
        dialog.exec()

    def start_knowledge_base_update(self):
        """开始更新知识库"""
        self.update_status("正在更新知识库...", "#607D8B")
        self.show_progress(True)
        self.docs_btn.setEnabled(False)

        # 清理之前的更新线程
        if self.update_kb_worker is not None:
            self.update_kb_worker.quit()
            self.update_kb_worker.wait()

        # 创建更新线程
        self.update_kb_worker = UpdateKnowledgeBaseWorker(self,model_name=self.model_name)
        self.update_kb_worker.finished.connect(self._on_update_kb_finished)
        self.update_kb_worker.error.connect(self._on_update_kb_error)
        self.update_kb_worker.output_update.connect(self._on_update_kb_output)
        self.update_kb_worker.start()

    def _on_update_kb_output(self, output):
        """更新知识库输出"""
        # 在聊天区域显示更新进度
        self.append_to_chat(f"更新进度: {output}")

    def _on_update_kb_finished(self,message):
        """更新知识库完成"""

        self.show_progress(False)
        self.docs_btn.setEnabled(True)
        self.update_status(message, "#4CAF50")

        # 显示完成消息
        QMessageBox.information(self, "更新完成", message)

        # 清理线程
        if self.update_kb_worker:
            self.update_kb_worker.deleteLater()
            self.update_kb_worker = None

    def _on_update_kb_error(self, error_msg):
        """处理知识库更新错误"""
        self.update_status("知识库更新失败", "#F44336")
        self.append_to_chat(f"知识库更新失败: {error_msg}")
        self.docs_btn.setEnabled(True)

    def on_model_changed(self, new_model):
        """处理模型选择变化"""
        self.rag_agent_factory.set_agent(None)
        # 获取选择的模型
        selected_model = self.model_combo.currentText()
        
        if "distiluse-base" in selected_model:
            self.model_name = "distiluse-base-multilingual-cased-v1"
        elif "all-MiniLM" in selected_model:
            self.model_name = "all-MiniLM-L6-v2"
        elif "bert-base-chinese" in selected_model:
            self.model_name = "bert-base-chinese"
        print(f"模型已更改为: {new_model}")

    def close_all_workers(self):
        """关闭所有工作线程"""
        if self.init_worker is not None:
            self.init_worker.quit()
            self.init_worker.wait()

        if self.query_worker is not None:
            self.query_worker.quit()
            self.query_worker.wait()

        if self.batch_worker is not None:
            self.batch_worker.quit()
            self.batch_worker.wait()

    def closeEvent(self, event):
        """窗口关闭事件，清理所有线程"""
        # 停止所有工作线程
        self.close_all_workers()

        event.accept()


def main():
    """主函数"""
    app = QApplication(sys.argv)

    # 设置应用信息
    app.setApplicationName("面向多学科学习的RAG智能助手")
    app.setApplicationVersion("2.0")
    app.setOrganizationName("RAG System")

    # 设置应用图标（如果有的话）
    app.setWindowIcon(QIcon("icon.png"))

    window = SimpleRAGTkApp()
    window.show()

    sys.exit(app.exec())


if __name__ == "__main__":
    main()
