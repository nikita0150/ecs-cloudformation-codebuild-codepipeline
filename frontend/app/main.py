from fastapi import FastAPI
import httpx
import os

app = FastAPI(title="ECS Production Frontend")

BACKEND_URL = os.environ["BACKEND_URL"]


@app.get("/")
def root():
    return {
        "application": "ECS Production Frontend",
        "version": "v1"
    }


@app.get("/health")
def health():
    return {
        "status": "healthy"
    }


@app.get("/backend-check")
def backend_check():
    try:
        response = httpx.get(
            f"{BACKEND_URL}/health",
            timeout=5
        )

        return {
            "frontend": "healthy",
            "backend": response.json()
        }

    except Exception as e:
        return {
            "frontend": "healthy",
            "backend": "unreachable",
            "error": str(e)
        }