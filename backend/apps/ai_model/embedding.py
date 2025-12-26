import os.path
import threading
from typing import Optional

from langchain_core.embeddings import Embeddings
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_community.embeddings import DashScopeEmbeddings
from pydantic import BaseModel
from modelscope import snapshot_download

from common.core.config import settings

os.environ["TOKENIZERS_PARALLELISM"] = "false"


class EmbeddingModelInfo(BaseModel):
    folder: Optional[str] = None
    name: str
    device: str = 'cpu'
    type: str = 'local'
    api_key: Optional[str] = None


# 这里的 name 修改为 ModelScope 上的模型 ID
# local_embedding_model = EmbeddingModelInfo(
#     folder=settings.LOCAL_MODEL_PATH,
#     name="zjwan461/shibing624_text2vec-base-chinese",  # ModelScope 的模型 ID
#     device='cpu'
# )

# 方案 B: 使用 Qwen (通义千问) API
# 请确保环境变量 DASHSCOPE_API_KEY 已设置，或者直接填入 api_key
local_embedding_model = EmbeddingModelInfo(
    type='qwen',
    name="text-embedding-v4", # Qwen 的 embedding 模型名称
    api_key="sk-0da558b660674d28955434ce0f7fadd8" # 替换为你的阿里云 API Key
)

_lock = threading.Lock()
locks = {}

_embedding_model: dict[str, Optional[Embeddings]] = {}


class EmbeddingModelCache:

    @staticmethod
    def _new_instance(config: EmbeddingModelInfo = local_embedding_model):
        if config.type == 'qwen':
            # 使用阿里云 DashScope (Qwen)
            return DashScopeEmbeddings(
                model=config.name,
                dashscope_api_key=config.api_key
            )
        else:
            model_dir = snapshot_download(
                model_id=config.name,
                cache_dir=config.folder
            )
            return HuggingFaceEmbeddings(model_name=model_dir, cache_folder=config.folder,
                                         model_kwargs={'device': config.device},
                                         encode_kwargs={'normalize_embeddings': True}
                                         )

    @staticmethod
    def _get_lock(key: str = settings.DEFAULT_EMBEDDING_MODEL):
        lock = locks.get(key)
        if lock is None:
            with _lock:
                lock = locks.get(key)
                if lock is None:
                    lock = threading.Lock()
                    locks[key] = lock

        return lock

    @staticmethod
    def get_model(key: str = settings.DEFAULT_EMBEDDING_MODEL,
                  config: EmbeddingModelInfo = local_embedding_model) -> Embeddings:
        model_instance = _embedding_model.get(key)
        if model_instance is None:
            lock = EmbeddingModelCache._get_lock(key)
            with lock:
                model_instance = _embedding_model.get(key)
                if model_instance is None:
                    model_instance = EmbeddingModelCache._new_instance(config)
                    _embedding_model[key] = model_instance

        return model_instance
