from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from controllers.loan_controller import update_loans_status
from routes.routes import api_router
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from websocket_manager.router_socket import ws_router
import os


app = FastAPI(
    title="API de Préstamos",
    description="API para gestión de préstamos con FastAPI y MongoDB",
    version="1.0"
)

# Configuración de CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(api_router)
app.include_router(ws_router)

# Inicializar scheduler global
scheduler = AsyncIOScheduler()

@app.on_event("startup")
async def startup_event():
    # Aquí ya hay un event loop activo
    scheduler.add_job(update_loans_status, 'cron', hour='19', minute='10') 
    scheduler.start()
    print("✅ Scheduler iniciado correctamente")



if os.getenv("ENV") != "production":
    import uvicorn

    if __name__ == "__main__":
        uvicorn.run("app:app", host="0.0.0.0", port=int(os.getenv("PORT", 8000)), reload=True)

