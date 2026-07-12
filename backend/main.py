import logging

from dotenv import load_dotenv

load_dotenv()
logging.basicConfig(level=logging.INFO)

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from backend.routers.recipes import router as recipes_router

app = FastAPI()

origins = [
    "http://localhost:5173",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(recipes_router)

app.frontend("/", directory="frontend/dist", fallback="index.html", check_dir=False)