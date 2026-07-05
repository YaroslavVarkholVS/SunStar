import json
import logging
from typing import Any

import openai
from langchain.agents import create_agent
from langchain.messages import HumanMessage
from langchain_core.messages import AIMessageChunk
from langchain_core.tools import tool
from langchain_openai import ChatOpenAI
from tavily import TavilyClient
from backend.recipe_store import RecipeStoreError, search_recipes

logger = logging.getLogger(__name__)

SYSTEM_PROMPT = """You are a recipe search assistant.
First call search_saved_recipes ONCE to look for recipes the user has already saved that match the ingredients.
If it returns relevant matches, base your answer on those and do NOT call web_search.
Only call web_search, and ONLY ONCE, if search_saved_recipes has no relevant matches.
Return ONLY a bullet-point list of recipe names and very brief, ultra-concise steps + links to the recipes if available.
Do not include introductions, or conclusions. Be brief to save tokens."""

_tavily_client = TavilyClient()


@tool
def web_search(query: str) -> dict[str, Any]:
    """Search the web for the given query and return matching results."""
    return _tavily_client.search(query)


@tool
def search_saved_recipes(query: str) -> list[dict[str, Any]]:
    """Search the user's saved recipes for the given query.

    Returns a list of genuine matches, each with a recipe name and its full
    text. Returns an empty list if nothing is saved, nothing is a close
    enough match, or the search is temporarily unavailable.
    """
    try:
        return search_recipes(query)
    except RecipeStoreError:
        return []


llm = ChatOpenAI(
    model="gpt-5-nano",
    # Minimize money flow
    temperature=0.0,
    max_tokens=150,
    verbosity="low",
    reasoning_effort="minimal",
)

agent = create_agent(
    model=llm,
    tools=[search_saved_recipes, web_search],
    system_prompt=SYSTEM_PROMPT,
)


def _event(**fields: Any) -> str:
    return json.dumps(fields) + "\n"


async def stream_recipe_tokens(ingredients: str):
    try:
        async for message_chunk, _metadata in agent.astream(
            {"messages": [HumanMessage(content=ingredients)]},
            stream_mode="messages",
        ):
            if isinstance(message_chunk, AIMessageChunk) and message_chunk.content:
                yield _event(type="token", content=message_chunk.content)
    except openai.APIStatusError as e:
        yield _event(type="error", detail=f"The recipe assistant failed to respond: {e.message}")
        return
    except openai.APIConnectionError:
        yield _event(type="error", detail="The recipe assistant is temporarily unavailable. Please try again later.")
        return
    except Exception:
        logger.exception("Unhandled error while streaming recipe search")
        yield _event(type="error", detail="Something went wrong. Please try again later.")
        return

    yield _event(type="done")
