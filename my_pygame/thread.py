# -*- coding: Utf-8 -*

from threading import Thread
from functools import wraps

def threaded_function(function):

    @wraps(function)
    def wrapper(*args, **kwargs) -> Thread:
        thread = Thread(target=function, args=args, kwargs=kwargs, daemon=True)
        thread.start()
        return thread
    
    return wrapper