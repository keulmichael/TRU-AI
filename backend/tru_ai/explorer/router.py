from __future__ import annotations

from pathlib import Path

from fastapi import APIRouter
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles


STATIC_DIRECTORY = Path(__file__).resolve().parent / "static"

router = APIRouter(tags=["Graph explorer"])
router.mount(
    "/explorer/static",
    StaticFiles(directory=STATIC_DIRECTORY),
    name="graph-explorer-static",
)


@router.get("/explorer")
def graph_explorer() -> FileResponse:
    return FileResponse(
        STATIC_DIRECTORY / "explorer.html"
    )
