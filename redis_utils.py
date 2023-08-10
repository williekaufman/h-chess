import redis as r
from typing import Optional, Any

redis = r.Redis(connection_pool=r.ConnectionPool(host='localhost', port=6379, db=0))

def rget(key: str, *, game_id: Optional[str]) -> Optional[str]:
    key = f'hchess:{key}'
    if game_id is None:
        raw_result = redis.get(key)
    else:
        raw_result = redis.get(f'{game_id}:{key}')
    return raw_result.decode('utf-8') if raw_result is not None else None

def rset(key: str, value: Any, *, game_id: Optional[str], ex: Optional[int] = 86400) -> None:
    key = f'hchess:{key}'
    if game_id is None:
        redis.set(key, value, ex=ex)    
    else:
        redis.set(f'{game_id}:{key}', value, ex=ex)
