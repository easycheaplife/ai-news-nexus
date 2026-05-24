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
    更加鲁棒的键生成器：
    1. 优先使用 Request URL 和 Query Params，这对于 API 接口是最稳定且唯一的标识。
    2. 自动忽略 db (Session) 等注入的后台对象。
    """
    from fastapi_cache import FastAPICache
    prefix = FastAPICache.get_prefix()
    
    if request:
        # 使用完整的路径和查询字符串作为键
        # 例如: /api/news/?platform=twitter&limit=50
        url_key = f"{request.url.path}:{request.query_params}"
        key = f"{prefix}:{namespace}:{url_key}"
    else:
        # 兜底逻辑：手动排除非数据参数
        cache_kwargs = {k: v for k, v in kwargs.items() if k not in ['db', 'request', 'response']}
        key = f"{prefix}:{namespace}:{func.__module__}:{func.__name__}:{cache_kwargs}"
        
    return hashlib.md5(key.encode()).hexdigest()
