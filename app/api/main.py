from fastapi import FastAPI

app = FastAPI(
    title="social-chatbot-core API",
    version="0.1.0",
    description="Interanl API para el chatbot social core project"
)

@app.get("/")
def root() -> dict:
    return {
        "message": "social-chatbot-core API is running",
        "status": "ok"
    }

