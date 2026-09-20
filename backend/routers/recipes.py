from fastapi import APIRouter, HTTPException
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field
from http import HTTPStatus
from uuid import uuid4

from backend.agent import stream_recipe_tokens, resume_recipe_search_stream
from langgraph.types import Command
from backend.agent import recipe_graph, _graph_config
from backend.recipe_store import RecipeStoreError, store_recipe

router = APIRouter()


class RecipeSearchRequest(BaseModel):
    ingredients: str


@router.post("/api/recipes/search")
async def search_recipes(payload: RecipeSearchRequest) -> StreamingResponse:
    thread_id = str(uuid4())

    return StreamingResponse(
        stream_recipe_tokens(
            payload.ingredients,
            thread_id,
        ),
        media_type="application/x-ndjson",
        headers={
            "X-Thread-ID": thread_id,
        },
    )


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


class RecipeApprovalRequest(BaseModel):
    thread_id: str
    approved: bool


@router.post("/api/recipes/search/resume")
async def resume_recipe_search(
    payload: RecipeApprovalRequest,
) -> StreamingResponse:

    return StreamingResponse(
        resume_recipe_search_stream(
            thread_id=payload.thread_id,
            approved=payload.approved,
        ),
        media_type="application/x-ndjson",
    )