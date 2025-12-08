from fastapi import FastAPI

app = FastAPI(
    title="Logistics Task Marketplace",
    description="API for a task-based logistics platform.",
    version="1.0.0"
)

@app.get("/")
def read_root():
    return {"message": "Welcome to the Logistics Task Marketplace API"}
