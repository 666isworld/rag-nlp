from langchain_community.document_loaders import PyPDFLoader, DirectoryLoader
from langchain_community.document_loaders import UnstructuredWordDocumentLoader
from langchain_community.document_loaders import TextLoader

def get_document_loader(docs_dir):
    """
    获取支持多种格式的文档加载器
    
    Args:
        docs_dir: 文档目录路径
        
    Returns:
        DirectoryLoader: 支持多种格式的目录加载器
    """
    # 使用多种加载器加载不同类型的文件
    loaders = {
        "**/*.pdf": PyPDFLoader,
        "**/*.docx": UnstructuredWordDocumentLoader,
        "**/*.doc": UnstructuredWordDocumentLoader,
        "**/*.txt": TextLoader
    }
    
    # 返回所有文档的列表
    all_documents = []
    for glob_pattern, loader_cls in loaders.items():
        loader = DirectoryLoader(
            docs_dir,
            glob=glob_pattern,
            loader_cls=loader_cls
        )
        # try:
        documents = loader.load()
        all_documents.extend(documents)
        print(f"已加载 {len(documents)} 个{glob_pattern[3:]}文件")
            # except Exception as e:
            #     print(f"加载{glob_pattern[3:]}文件时出错: {str(e)}")
    
    return all_documents
