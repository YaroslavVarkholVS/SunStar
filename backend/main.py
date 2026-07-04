from fastapi import Depends, FastAPI
from backend.data_objects import Item
from fastapi.middleware.cors import CORSMiddleware
from sqlmodel import SQLModel

from backend.dependencies import verify_token, engine
from backend.users.routers import router as users_router
from fastapi.staticfiles import StaticFiles


def create_db_and_tables():
    SQLModel.metadata.create_all(engine)



app = FastAPI(dependencies=[Depends(verify_token)])
app.include_router(users_router)
app.frontend("/", directory="frontend", fallback="404.html")
app.mount("/static", StaticFiles(directory="static"), name="static")


@app.on_event("startup")
def on_startup():
    create_db_and_tables()

origins = [
    "http://localhost.tiangolo.com",
    "https://localhost.tiangolo.com",
    "http://localhost",
    "http://localhost:8080",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# @app.get("/")
# async def root():
#     return {"message": "Hello World"}


@app.get("/hello/{name}")
async def say_hello(name: str):
    return {"message": f"Hello {name}"}


@app.get("/items/{item_id}")
async def read_item(item_id):
    return {"item_id": item_id}


@app.post("/items/")
async def create_item(item: Item):
    return item


