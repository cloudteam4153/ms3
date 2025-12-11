from fastapi import FastAPI
from resources import tasks_router, todo_router, followup_router, classifications_router
import uvicorn

app = FastAPI(
    title="Actions Service",
    description="Task management microservice for unified inbox",
    version="1.0.0"
)

# Register all resource routers
app.include_router(tasks_router)
app.include_router(todo_router)
app.include_router(followup_router)
app.include_router(classifications_router)


@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "healthy", "service": "actions-service"}


if __name__ == "__main__":
    import os
    port = int(os.getenv("PORT", 8080))
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=port,
        reload=True
    )

