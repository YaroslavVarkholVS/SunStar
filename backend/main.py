from typing import Any
from dotenv import load_dotenv

load_dotenv()

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
from sqlmodel import SQLModel, create_engine
from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser
from langchain_core.tools import tool
from langchain.agents import create_agent
from langgraph.checkpoint.memory import InMemorySaver
from tavily import TavilyClient
from langchain.messages import HumanMessage
import openai

engine = create_engine("sqlite:///database.db")


def create_db_and_tables():
    SQLModel.metadata.create_all(engine)


app = FastAPI()

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


@app.on_event("startup")
def on_startup():
    create_db_and_tables()


class RecipeSearchRequest(BaseModel):
    ingredients: str


class RecipeSearchResponse(BaseModel):
    recipes: list[str]


@tool
def web_search(query: str) -> dict[str, Any]:
    """Search the web for the given query and return matching results."""
    return TavilyClient().search(query)


system_prompt = """You are a helpful assistant that can search for recipes based on ingredients.
You will be given a list of ingredients, and you should return a list of recipes that can be made with those ingredients. 
You should use the web_search tool to find recipes online.
"""
config = {"configurable": {"thread_id": "1"}}

agent = create_agent(model="gpt-5-nano",
                     tools=[web_search],
                     system_prompt=system_prompt,
                     checkpointer=InMemorySaver()
                     )

@app.post("/api/recipes/search", response_model=RecipeSearchResponse)
async def search_recipes(payload: RecipeSearchRequest) -> RecipeSearchResponse:
    try:
        response = await agent.ainvoke({"messages": [HumanMessage(content=payload.ingredients)]}, config)
    except openai.RateLimitError:
        raise HTTPException(
            status_code=429,
            detail="The recipe assistant is temporarily unavailable because the OpenAI quota has been exceeded. Please try again later.",
        )
    except openai.AuthenticationError:
        raise HTTPException(
            status_code=502,
            detail="The recipe assistant is misconfigured (invalid OpenAI credentials). Please contact support.",
        )
    except openai.APIStatusError as e:
        raise HTTPException(
            status_code=502,
            detail=f"The recipe assistant failed to respond: {e.message}",
        )
    recipes = response["text"]

    return RecipeSearchResponse(recipes=[recipe.strip() for recipe in recipes.split("\n") if recipe.strip()])


app.mount("/static", StaticFiles(directory="static"), name="static")
app.mount("/", StaticFiles(directory="frontend/dist", html=True), name="frontend")

