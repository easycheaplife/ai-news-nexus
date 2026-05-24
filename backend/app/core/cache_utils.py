import hashlib
from typing import Optional
from fastapi import Request, Response

def nexus_key_builder(
    func,
    namespace: Optional[str] = "",
    request: Optional[Request] = None,
    response: Optional[Response] = None,
    args: Optional[tuple] = None,
    kwargs: Optional[dict] = None,
):
    """
    自定义键生成器：排除掉 'db' (Session) 等不可序列化或随请求变化的参数。
    """
    from fastapi_cache import FastAPICache
    
    # 提取有意义的参数，排除 'db'
    cache_kwargs = {k: v for k, v in kwargs.items() if k != 'db'}
    
    # 构造唯一标识字符串
    prefix = FastAPICache.get_prefix()
    key = f"{prefix}:{namespace}:{func.__module__}:{func.__name__}:{cache_kwargs}"
    
    return hashlib.md5(key.encode()).hexdigest()
