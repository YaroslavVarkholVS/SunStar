import json
import logging
from typing import Any, Literal, TypedDict

import openai
from langchain_core.messages import AIMessageChunk, HumanMessage, SystemMessage
from langchain_openai import ChatOpenAI
from langgraph.graph import END, START, StateGraph
from tavily import TavilyClient
from backend.recipe_store import RecipeStoreError, search_recipes

logger = logging.getLogger(__name__)

SAVED_RESULT_SYSTEM_PROMPT = """You are a recipe search assistant. Below are recipes the user has already saved that match their ingredients.
Return ONLY a bullet-point list of recipe names and very brief, ultra-concise steps + links to the recipes if available.
Do not include introductions, or conclusions. Be brief to save tokens."""

WEB_RESULT_SYSTEM_PROMPT = """You are a recipe search assistant. Below are web search results for the user's ingredients.
Return ONLY a bullet-point list of recipe names and very brief, ultra-concise steps + links to the recipes if available.
Do not include introductions, or conclusions. Be brief to save tokens."""

_tavily_client = TavilyClient()

llm = ChatOpenAI(
    model="gpt-5-nano",
    # Minimize money flow
    temperature=0.0,
    max_tokens=150,
    verbosity="low",
    reasoning_effort="minimal",
)


class RecipeSearchState(TypedDict, total=False):
    ingredients: str
    saved_matches: list[dict[str, Any]]
    web_results: dict[str, Any]
    answer: str


def _search_saved_node(state: RecipeSearchState) -> dict[str, Any]:
    try:
        matches = search_recipes(state["ingredients"])
    except RecipeStoreError:
        matches = []
    return {"saved_matches": matches}


def _route_after_saved(state: RecipeSearchState) -> Literal["respond", "web_search"]:
    return "respond" if state.get("saved_matches") else "web_search"


def _web_search_node(state: RecipeSearchState) -> dict[str, Any]:
    return {"web_results": _tavily_client.search(state["ingredients"])}


def _respond_node(state: RecipeSearchState) -> dict[str, Any]:
    if state.get("saved_matches"):
        system_prompt, data = SAVED_RESULT_SYSTEM_PROMPT, state["saved_matches"]
    else:
        system_prompt, data = WEB_RESULT_SYSTEM_PROMPT, state.get("web_results", {})

    response = llm.invoke(
        [
            SystemMessage(content=system_prompt),
            HumanMessage(content=f"Ingredients: {state['ingredients']}\n\nResults:\n{json.dumps(data)}"),
        ]
    )
    return {"answer": response.content}


_graph = StateGraph(RecipeSearchState)
_graph.add_node("search_saved", _search_saved_node)
_graph.add_node("web_search", _web_search_node)
_graph.add_node("respond", _respond_node)
_graph.add_edge(START, "search_saved")
_graph.add_conditional_edges("search_saved", _route_after_saved)
_graph.add_edge("web_search", "respond")
_graph.add_edge("respond", END)
recipe_graph = _graph.compile()


def _event(**fields: Any) -> str:
    return json.dumps(fields) + "\n"


async def stream_recipe_tokens(ingredients: str):
    try:
        async for message_chunk, _metadata in recipe_graph.astream(
            {"ingredients": ingredients},
            stream_mode="messages",
            config={"run_name": "recipe_search", "tags": ["recipe-search"]},
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
