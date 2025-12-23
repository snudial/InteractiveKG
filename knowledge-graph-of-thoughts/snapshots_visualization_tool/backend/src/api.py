






from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from routes.api_routes import API_ROUTES
app = FastAPI()
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
API_ROUTES(app)