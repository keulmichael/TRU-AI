from fastapi import FastAPI
from tru_ai.query.api import router as query_router
from tru_ai.reasoning.api import router as reasoning_router

app = FastAPI(
    title="TRU-AI",
    version="0.8.7.0",
    description="Artificial Intelligence for the Universal Reflexivity Theory",
)


@app.get("/")
def root():
    return {
        "name": "TRU-AI",
        "version": "0.8.7.0",
        "status": "running",
    }


app.include_router(query_router)
app.include_router(reasoning_router)
