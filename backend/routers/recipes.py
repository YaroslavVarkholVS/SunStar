from fastapi import APIRouter, HTTPException
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field
from http import HTTPStatus

from backend.agent import stream_recipe_tokens
from backend.recipe_store import RecipeStoreError, store_recipe

router = APIRouter()


class RecipeSearchRequest(BaseModel):
    ingredients: str


@router.post("/api/recipes/search")
async def search_recipes(payload: RecipeSearchRequest) -> StreamingResponse:
    return StreamingResponse(stream_recipe_tokens(payload.ingredients), media_type="application/x-ndjson")


class RecipeSaveRequest(BaseModel):
    model_config = {"str_strip_whitespace": True}

    name: str = Field(min_length=1)
    recipe: str = Field(min_length=1)


class RecipeSaveResponse(BaseModel):
    message: str
    status_code: HTTPStatus


@router.post("/api/recipes/save")
async def save_recipe(payload: RecipeSaveRequest) -> RecipeSaveResponse:
    try:
        store_recipe(payload.name, payload.recipe)
    except RecipeStoreError as e:
        raise HTTPException(status_code=503, detail=str(e)) from e

    return RecipeSaveResponse(message="Recipe saved successfully", status_code=HTTPStatus.OK)
