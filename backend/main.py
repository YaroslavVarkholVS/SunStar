import json
import logging
from typing import Any

from dotenv import load_dotenv

load_dotenv()

import openai
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from langchain.agents import create_agent
from langchain.messages import HumanMessage
from langchain_core.messages import AIMessageChunk
from langchain_core.tools import tool
from langchain_openai import ChatOpenAI
from tavily import TavilyClient

logger = logging.getLogger(__name__)

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


class RecipeSearchRequest(BaseModel):
    ingredients: str


@tool
def web_search(query: str) -> dict[str, Any]:
    """Search the web for the given query and return matching results."""
    return TavilyClient().search(query)


system_prompt = """You are a recipe search assistant. 
Find recipes based on provided ingredients using the web_search tool ONLY ONCE per query.
Return ONLY a bullet-point list of recipe names and very brief, ultra-concise steps.
Do not include links, introductions, or conclusions. Be brief to save tokens."""


llm = ChatOpenAI(
    model="gpt-5-nano",
    # Minimize money flow
    temperature=0.0,
    max_tokens=150,
    verbosity="low",
    reasoning_effort="minimal"
)

agent = create_agent(
    model=llm,
    tools=[web_search],
    system_prompt=system_prompt,
)


async def stream_recipe_tokens(ingredients: str):
    try:
        async for message_chunk, _metadata in agent.astream(
            {"messages": [HumanMessage(content=ingredients)]},
            stream_mode="messages",
        ):
            if isinstance(message_chunk, AIMessageChunk) and message_chunk.content:
                yield json.dumps({"type": "token", "content": message_chunk.content}) + "\n"
    except openai.APIStatusError as e:
        yield json.dumps({"type": "error", "detail": f"The recipe assistant failed to respond: {e.message}"}) + "\n"
        return
    except openai.APIConnectionError:
        yield json.dumps({"type": "error", "detail": "The recipe assistant is temporarily unavailable. Please try again later."}) + "\n"
        return
    except Exception:
        logger.exception("Unhandled error while streaming recipe search")
        yield json.dumps({"type": "error", "detail": "Something went wrong. Please try again later."}) + "\n"
        return

    yield json.dumps({"type": "done"}) + "\n"


@app.post("/api/recipes/search")
async def search_recipes(payload: RecipeSearchRequest) -> StreamingResponse:
    return StreamingResponse(stream_recipe_tokens(payload.ingredients), media_type="application/x-ndjson")


app.frontend("/", directory="frontend/dist", fallback="index.html", check_dir=False)