from fastapi import FastAPI
from tru_ai.query.api import router as query_router

app = FastAPI(
    title="TRU-AI",
    version="0.8.5.1",
    description="Artificial Intelligence for the Universal Reflexivity Theory",
)


@app.get("/")
def root():
    return {
        "name": "TRU-AI",
        "version": "0.8.5.1",
        "status": "running",
    }


app.include_router(query_router)