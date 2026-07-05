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

logger = logging.getLogger(__name__)

SYSTEM_PROMPT = """You are a recipe search assistant.
Find recipes based on provided ingredients using the web_search tool ONLY ONCE per query.
Return ONLY a bullet-point list of recipe names and very brief, ultra-concise steps.
Do not include links, introductions, or conclusions. Be brief to save tokens."""

_tavily_client = TavilyClient()


@tool
def web_search(query: str) -> dict[str, Any]:
    """Search the web for the given query and return matching results."""
    return _tavily_client.search(query)


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
    tools=[web_search],
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
