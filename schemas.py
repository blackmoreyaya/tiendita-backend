from pydantic import BaseModel
from datetime import datetime
from typing import Optional

# Esquema base con los datos comunes
class ProductoBase(BaseModel):
    nombre: str
    precio: float
    stock: int = 0
    status: bool = True

# Esquema para CREAR un producto (por ahora es igual al base)
class ProductoCreate(ProductoBase):
    pass

# Esquema para RESPONDER (incluye el ID que genera Postgres)
class ProductoResponse(ProductoBase):
    id: str # <--- Cambió de int a str para soportar el UUID
    created_at: datetime # <--- Agregamos la fecha de creación
    updated_at: datetime # <--- Agregamos la fecha de actualización

    class Config:
        from_attributes = True  # Esto permite que Pydantic lea el modelo de SQLAlchemy


class VentaBase(BaseModel):
    producto_id: str
    cantidad: int = 0
    status: bool = True
    es_muestra: bool = False

class VentaCreate(VentaBase):
    pass

class VentaResponse(VentaBase):
    id: str # <--- Cambió de int a str para soportar el UUID
    fecha_venta: datetime
    created_at: datetime # <--- Agregamos la fecha de creación
    updated_at: datetime # <--- Agregamos la fecha de actualización

    class Config:
        from_attributes = True  # Esto permite que Pydantic lea el modelo de SQLAlchemy

class ProductoUpdate(BaseModel):
    nombre: Optional[str] = None
    precio: Optional[float] = None
    stock: Optional[int] = None