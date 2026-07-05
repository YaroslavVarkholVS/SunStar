import logging
from typing import Any

from langchain_chroma import Chroma
from langchain_openai import OpenAIEmbeddings

logger = logging.getLogger(__name__)

# Empirically, genuine ingredient matches land around 0.2-0.3 distance while
# unrelated recipes sit above 0.4 (see the ada-002 embeddings used here).
MAX_MATCH_DISTANCE = 0.4


class RecipeStoreError(Exception):
    """Raised when a recipe cannot be persisted to the vector store."""


_vectorstore = Chroma(
    collection_name="recipes",
    embedding_function=OpenAIEmbeddings(),
    persist_directory="./chroma_recipes",
)


def store_recipe(name: str, recipe: str) -> None:
    try:
        _vectorstore.add_texts(texts=[recipe], metadatas=[{"name": name}])
    except Exception as e:
        logger.exception("Failed to store recipe %r", name)
        raise RecipeStoreError("The recipe couldn't be saved right now. Please try again later.") from e


def search_recipes(query: str, k: int = 5) -> list[dict[str, Any]]:
    try:
        results = _vectorstore.similarity_search_with_score(query, k=k)
    except Exception as e:
        logger.exception("Failed to search saved recipes for query %r", query)
        raise RecipeStoreError("Could not search saved recipes right now.") from e

    return [
        {"name": document.metadata.get("name"), "recipe": document.page_content, "distance": score}
        for document, score in results
        if score <= MAX_MATCH_DISTANCE
    ]
