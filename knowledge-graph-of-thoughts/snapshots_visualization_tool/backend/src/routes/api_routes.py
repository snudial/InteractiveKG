






from fastapi import FastAPI
from . import _API_DATABASE
class API_ROUTES:
    def __init__(self, app: FastAPI) -> None:
        _API_DATABASE(app)