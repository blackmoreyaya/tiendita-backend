from fastapi import FastAPI
from database import engine, Base
from fastapi.middleware.cors import CORSMiddleware
import models

# Importamos nuestros nuevos routers
from routers import productos
from routers import ventas
from routers import agente

# Esto crea las tablas en la base de datos si no existen (como php artisan migrate)
Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="Agente de Inventario API",
    description="Backend para el sistema de predicción de la tiendita",
    version="2.0.0"
)

# Configuramos el CORS para permitir que React se conecte
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], # En producción aquí pondrías la URL de tu frontend
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# --- INCLUIMOS LAS RUTAS (Como registrar los controladores) ---
app.include_router(productos.router)
app.include_router(ventas.router)
app.include_router(agente.router)



@app.get("/")
def leer_raiz():
    return {"mensaje": "¡El cerebro de la tiendita está vivo!"}
