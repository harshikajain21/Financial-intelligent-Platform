# api/limiter.py

from slowapi import Limiter
from slowapi.util import get_remote_address

# Rate limiter — identifies clients by IP address
limiter = Limiter(key_func=get_remote_address)