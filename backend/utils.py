import time
import logging
from functools import wraps

logger = logging.getLogger(__name__)

def timeit(func):
    @wraps(func)
    def wrapper(*args, **kwargs):
        start_time = time.time()
        result = func(*args, **kwargs)
        end_time = time.time() 
        
        # 计算执行时间
        execution_time = duration_readable(end_time - start_time)
        logger.debug(f"call {func.__name__} {execution_time}")
        
        return result
    return wrapper

def duration_readable(s:float) -> str:
    ms = int(s * 1000)
    if ms == 0:
        return "1 ms"
    if ms < 1500:
        return f"{ms} ms"
    if s < 60:
        return f"{s:.3f} s"
    m = s/60.
    return f"{m:.3f} m"