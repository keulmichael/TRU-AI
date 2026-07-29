from fastapi import FastAPI
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from pathlib import Path
from tru_ai.cognitive.api import router as cognitive_router
from tru_ai.exploration.api import router as exploration_router
from tru_ai.explorer.router import router as explorer_router
from tru_ai import __version__
from tru_ai.query.api import router as query_router
from tru_ai.reasoning.api import router as reasoning_router

app = FastAPI(
    title="TRU-AI",
    version=__version__,
    description="Artificial Intelligence for the Universal Reflexivity Theory",
)

COGNITIVE_STATIC_DIRECTORY = (
    Path(__file__).resolve().parents[1]
    / "cognitive"
    / "static"
)
app.mount(
    "/cognitive/static",
    StaticFiles(directory=COGNITIVE_STATIC_DIRECTORY),
    name="cognitive-static",
)


@app.get("/")
def root():
    return FileResponse(
        COGNITIVE_STATIC_DIRECTORY / "cognitive.html"
    )


@app.get("/scientific-demo")
def scientific_demo_page():
    return FileResponse(
        COGNITIVE_STATIC_DIRECTORY / "scientific-demo.html"
    )


app.include_router(cognitive_router)
app.include_router(query_router)
app.include_router(reasoning_router)
app.include_router(exploration_router)
app.include_router(explorer_router)
