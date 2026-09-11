from fastapi import FastAPI

app = FastAPI(title="ECS Production Backend")


@app.get("/health")
def health():
    return {
        "status": "healthy"
    }


@app.get("/api/message")
def message():
    return {
        "message": "Hello from the ECS backend",
        "service": "backend",
        "version": "v1"
    }