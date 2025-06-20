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

scheduler = AsyncIOScheduler()

@app.on_event("startup")
async def startup_event():
    # Job liviano para "mantener vivo" el servidor cada 15 min
    scheduler.add_job(lambda: print("🟢 Reactivando servidor..."), 'interval', minutes=15)

    # Job pesado para update de préstamos cada 6 horas
    scheduler.add_job(update_loans_status, 'interval', hours=6)

    scheduler.start()
    print("✅ Scheduler iniciado correctamente")

@app.get("/")
def root():
    return {"message": "🚀 API de Préstamos activa"}

if os.getenv("ENV") != "production":
    import uvicorn

    if __name__ == "__main__":
        uvicorn.run("app:app", host="0.0.0.0", port=int(os.getenv("PORT", 8000)), reload=True)

