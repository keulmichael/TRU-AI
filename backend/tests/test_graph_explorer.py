from fastapi import FastAPI
from fastapi.testclient import TestClient

from tru_ai.explorer.router import router


def test_explorer_page_available() -> None:
    app = FastAPI()
    app.include_router(router)
    client = TestClient(app)

    response = client.get("/explorer")

    assert response.status_code == 200
    assert "TRU-AI Graph Explorer" in response.text


def test_explorer_static_files_available() -> None:
    app = FastAPI()
    app.include_router(router)
    client = TestClient(app)

    assert client.get(
        "/explorer/static/explorer.css"
    ).status_code == 200
    js = client.get(
        "/explorer/static/explorer.js"
    )
    assert js.status_code == 200
    assert "fetch(" in js.text
    assert "https://" not in js.text
