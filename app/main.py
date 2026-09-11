from fastapi import FastAPI

app = FastAPI(title="ECS CI/CD Demo")


@app.get("/")
def root():
    return {
        "message": "ECS CI/CD Demo",
        "version": "v1"
    }


@app.get("/health")
def health():
    return {
        "status": "healthy"
    }


@app.get("/info")
def info():
    return {
        "application": "ECS CI/CD Demo",
        "environment": "production",
        "version": "v1"
    }
