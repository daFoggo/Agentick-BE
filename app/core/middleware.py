from functools import wraps

from app.services.base_service import BaseService


def inject(func):
    @wraps(func)
    def wrapper(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        finally:
            injected_services = [arg for arg in kwargs.values() if isinstance(arg, BaseService)]
            if not injected_services:
                return
            try:
                injected_services[-1].close_scoped_session()
            except Exception:
                pass

    return wrapper
