from fastapi import APIRouter
from fastapi.responses import StreamingResponse
from pydantic import BaseModel

from backend.agent import stream_recipe_tokens

router = APIRouter()


class RecipeSearchRequest(BaseModel):
    ingredients: str


@router.post("/api/recipes/search")
async def search_recipes(payload: RecipeSearchRequest) -> StreamingResponse:
    return StreamingResponse(stream_recipe_tokens(payload.ingredients), media_type="application/x-ndjson")
