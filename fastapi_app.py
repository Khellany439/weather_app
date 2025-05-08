from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.openapi.docs import get_swagger_ui_html
from fastapi.openapi.utils import get_openapi
from fastapi import Depends

from database import engine
import models
from routers.users import router as users_router
from routers.weather import router as weather_router
from routers.credits import router as credits_router
from auth import get_current_user

# Create database tables
models.Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="Weather Information Cloud Service",
    description="API for weather information retrieval with credit system and user authentication",
    version="1.0.0",
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allow all origins in development
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(users_router, prefix="/api/users", tags=["users"])
app.include_router(weather_router, prefix="/api/weather", tags=["weather"])
app.include_router(credits_router, prefix="/api/credits", tags=["credits"])

@app.get("/", tags=["root"])
async def root():
    """Endpoint to check if the API is running"""
    return {"message": "Weather Information Cloud Service API is running"}

@app.get("/api/status", tags=["status"])
async def status(current_user: models.User = Depends(get_current_user)):
    """Endpoint to check if the user is authenticated"""
    return {
        "status": "authenticated", 
        "user_id": current_user.id, 
        "username": current_user.username,
        "credits": current_user.credits
    }

@app.get("/api/docs", include_in_schema=False)
async def custom_swagger_ui_html():
    return get_swagger_ui_html(
        openapi_url=app.openapi_url,
        title=f"{app.title} - API Documentation",
        swagger_js_url="https://cdn.jsdelivr.net/npm/swagger-ui-dist@5/swagger-ui-bundle.js",
        swagger_css_url="https://cdn.jsdelivr.net/npm/swagger-ui-dist@5/swagger-ui.css",
    )

@app.get("/api/openapi.json", include_in_schema=False)
async def get_open_api_endpoint():
    return get_openapi(
        title=app.title,
        version=app.version,
        description=app.description,
        routes=app.routes,
    )