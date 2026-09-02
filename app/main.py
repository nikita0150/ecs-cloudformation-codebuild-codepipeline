from fastapi import FastAPI

app = FastAPI(
    title="ECS CI/CD Demo",
    description="Demo application for AWS ECS deployment",
    version="1.0.0"
)


@app.get("/")
def home():
    return {
        "message": "Hello from ECS!",
        "version": "v1"
    }


@app.get("/health")
def health_check():
    return {
        "status": "healthy"
    }


@app.get("/info")
def application_info():
    return {
        "application": "ECS CI/CD Demo",
        "environment": "development",
        "version": "v1"
    }