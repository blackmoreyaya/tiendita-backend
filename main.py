from fastapi import FastAPI
from database import engine, Base
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

# --- INCLUIMOS LAS RUTAS (Como registrar los controladores) ---
app.include_router(productos.router)
app.include_router(ventas.router)
app.include_router(agente.router)



@app.get("/")
def leer_raiz():
    return {"mensaje": "¡El cerebro de la tiendita está vivo!"}
