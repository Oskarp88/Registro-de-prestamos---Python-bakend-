from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from routes.routes import api_router

app = FastAPI(
    title="API de Préstamos",
    description="API para gestión de préstamos con FastAPI y MongoDB",
    version="1.0"
)
# Configuración de CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # O podrías poner ["http://localhost:8000", "http://192.168.2.6:8000"] si querés restringirlo
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(api_router)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app:app", host="0.0.0.0", port=8000, reload=True)
