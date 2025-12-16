from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles

from app.core.config import settings
from app.routers import admin, auth, business, permission, task, user, wallet

app = FastAPI(
    title="Logistics Task Marketplace",
    description="API for a task-based logistics platform.",
    version="1.0.0"
)

app.include_router(auth.router, prefix="/auth", tags=["auth"])
app.include_router(user.router, prefix="/users", tags=["users"])
app.include_router(task.router, prefix="/tasks", tags=["tasks"])
app.include_router(wallet.router, prefix="/wallet", tags=["wallet"])
app.include_router(admin.router, prefix="/admin", tags=["admin"])
app.include_router(permission.router, prefix="/permissions", tags=["permissions"])
app.include_router(business.router, prefix="/admin/businesses", tags=["businesses"])

app.mount(settings.MEDIA_BASE_URL, StaticFiles(directory=settings.MEDIA_ROOT), name="media")


@app.get("/")
def read_root():
    return {"message": "Welcome to the Logistics Task Marketplace API"}
