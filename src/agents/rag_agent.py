"""
全新修复版本的RAG代理，解决所有已知问题
"""
import os
from typing import List, Tuple, Any, Dict
from dotenv import load_dotenv

# 使用最新的包路径
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_chroma import Chroma
from langchain.memory import ConversationBufferMemory
from langchain_openai import ChatOpenAI
from langchain.chains import ConversationalRetrievalChain
from langchain.docstore.document import Document
from langchain_community.document_loaders import PyPDFLoader, DirectoryLoader

# 导入文档加载器工具
from src.utils.document_loaders import get_document_loader

class RAGAgent:
    def __init__(
        self, 
        docs_dir: str = "docs", 
        persist_dir: str = "db", 
        api_base: str = None, 
        api_key: str = None
    ):
        """
        初始化RAG代理
        
        Args:
            docs_dir: 文档目录
            persist_dir: 向量存储持久化目录
            api_base: API基础URL
            api_key: API密钥
        """
        load_dotenv()
        
        self.docs_dir = docs_dir
        self.persist_dir = persist_dir
        
        # 创建目录（如果不存在）
        os.makedirs(docs_dir, exist_ok=True)
        os.makedirs(persist_dir, exist_ok=True)
        
        # 初始化组件
        self.embeddings = HuggingFaceEmbeddings(model_name="E:/code/python/rag-knowledge-base/models/all-MiniLM-L6-v2")
        self.text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=1000,
            chunk_overlap=200
        )
        
        # 初始化向量存储
        self.vector_store = self._initialize_vector_store()
        
        # 使用自定义API初始化LLM（如果提供）
        if api_base and api_key:
            self.llm = ChatOpenAI(
                temperature=0.7,
                openai_api_base=api_base,
                openai_api_key=api_key
            )
        else:
            self.llm = ChatOpenAI(temperature=0.7)
        
        # 初始化检索链
        self.qa_chain = ConversationalRetrievalChain.from_llm(
            llm=self.llm,
            retriever=self.vector_store.as_retriever(),
        )

    def _initialize_vector_store(self) -> Chroma:
        """初始化或加载向量存储。"""
        # 检查向量存储是否存在
        if os.path.exists(self.persist_dir) and os.listdir(self.persist_dir):
            return Chroma(
                persist_directory=self.persist_dir,
                embedding_function=self.embeddings
            )
        
        # 使用增强的文档加载器
        documents = get_document_loader(self.docs_dir)
        
        if not documents:
            print(f"警告: 在{self.docs_dir}目录中未找到任何文档")
            return Chroma(
                persist_directory=self.persist_dir,
                embedding_function=self.embeddings
            )
        
        # 拆分文档
        splits = self.text_splitter.split_documents(documents)
        
        # 创建并持久化向量存储
        vector_store = Chroma.from_documents(
            documents=splits,
            embedding=self.embeddings,
            persist_directory=self.persist_dir
        )
        # vector_store.persist()
        return vector_store

    def query(self, question: str) -> str:
        """
        使用问题查询RAG系统。
        
        Args:
            question: 用户问题
            
        Returns:
            str: 回答文本
        """
        # 提供空的chat_history参数
        response = self.qa_chain.invoke({
            "question": question, 
            "chat_history": []
        })
        return response["answer"]

    def query_with_sources(self, question: str) -> Tuple[str, List[Document]]:
        """
        查询知识库并返回答案和源文档
        
        Args:
            question: 用户问题
            
        Returns:
            tuple: (回答文本, 源文档列表)
        """
        # 嵌入问题
        question_embedding = self.embeddings.embed_query(question)
        
        # 获取相似文档
        docs = self.vector_store.similarity_search_by_vector(question_embedding, k=4)
        
        # 构建提示
        context = "\n\n".join([doc.page_content for doc in docs])
        prompt = f"""基于以下信息回答问题。如果信息中找不到答案，请说"我没有足够的信息来回答这个问题"。
        
        信息:
        {context}
        
        问题: {question}
        
        回答:"""
        
        response = self.get_completion(prompt)
        
        return response, docs

    def get_completion(self, prompt: str) -> str:
        """使用LLM获取对提示的响应"""
        return self.llm.predict(prompt)

    def ingest_documents(self) -> None:
        """重新初始化带有当前文档的向量存储。"""
        # 先清理现有连接
        self.cleanup()

        if os.path.exists(self.persist_dir):
            import shutil
            shutil.rmtree(self.persist_dir)
        self.vector_store = self._initialize_vector_store()

    def cleanup(self):
        """清理资源，关闭数据库连接"""
        try:
            if hasattr(self, 'vector_store') and self.vector_store:
                # 尝试关闭Chroma连接
                if hasattr(self.vector_store, '_client'):
                    # if hasattr(self.vector_store._client, 'reset'):
                    #     self.vector_store._client.reset()
                    if hasattr(self.vector_store._client, '_system'):
                        if hasattr(self.vector_store._client._system, 'stop'):
                            self.vector_store._client._system.stop()

                # 删除向量存储引用
                del self.vector_store
                self.vector_store = None

        except Exception as e:
            print(f"清理资源时出现警告: {e}")

    def __del__(self):
        """析构函数，确保资源被清理"""
        self.cleanup()

    def get_completion(self, prompt):
        '''使用LLM获取对提示的响应'''
        return self.llm.predict(prompt)