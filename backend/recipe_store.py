import logging

from langchain_chroma import Chroma
from langchain_openai import OpenAIEmbeddings

logger = logging.getLogger(__name__)


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
