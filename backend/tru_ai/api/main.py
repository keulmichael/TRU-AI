from fastapi import FastAPI

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