"""
RAG系统的提示词模板管理模块
"""

class RAGPromptTemplates:
    """提供RAG系统使用的各种提示词模板"""
    
    @staticmethod
    def get_chinese_qa_template():
        """获取中文问答提示词模板"""
        return """你是一个面向多学科学习的RAG智能助手，你的任务是根据提供的文档内容回答用户问题。
        
文档内容:
{context}

请根据上述文档内容，准确、简洁地回答以下问题。如果文档中没有相关信息，请明确说明"根据提供的文档内容，我无法回答这个问题"。不要编造不在文档中的信息。

用户问题: {question}

回答:"""

    @staticmethod
    def get_english_qa_template():
        """获取英文问答提示词模板"""
        return """You are an intelligent assistant. Your task is to answer the user's question based on the provided document content.
        
Document content:
{context}

Based on the document content above, please answer the following question accurately and concisely. If the information is not available in the document, clearly state "Based on the provided documents, I cannot answer this question." Do not make up information that is not in the document.

User question: {question}

Answer:"""

    @staticmethod
    def get_summary_template():
        """获取文档摘要提示词模板"""
        return """请根据以下文档内容，提供一个简洁、全面的摘要，包含文档的主要内容和要点。

文档内容:
{context}

摘要:"""

    @staticmethod
    def get_chinese_template_with_history():
        """获取带历史对话的中文提示词模板"""
        return """你是一个面向多学科学习的RAG智能助手，你的任务是根据提供的文档内容回答用户问题。
        
文档内容:
{context}

历史对话:
{history}

请根据上述文档内容和历史对话，准确、简洁地回答以下问题。如果文档中没有相关信息，请明确说明"根据提供的文档内容，我无法回答这个问题"。不要编造不在文档中的信息。

用户问题: {question}

回答:"""
