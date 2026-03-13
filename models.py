import uuid
from sqlalchemy import Column, Integer, String, Float, Boolean, DateTime, ForeignKey
from sqlalchemy.sql import func
from database import Base

class Producto(Base):
    __tablename__ = "productos"
    # Cambiamos a String y le decimos que genere un UUID automáticamente
    id = Column(String(36), primary_key=True, index=True, default=lambda: str(uuid.uuid4()))
    nombre = Column(String, index=True)
    precio = Column(Float)
    stock = Column(Integer, default=0)
    status = Column(Boolean, default=True)
    # El equivalente a los timestamps() de Laravel
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())


class Venta(Base):
    __tablename__ = "ventas"
    # Cambiamos a String y le decimos que genere un UUID automáticamente
    id = Column(String(36), primary_key=True, index=True, default=lambda: str(uuid.uuid4()))
    producto_id = Column(String(36), ForeignKey("productos.id"))
    cantidad = Column(Integer, default=0)
    fecha_venta = Column(DateTime(timezone=True), server_default=func.now())
    status = Column(Boolean, default=True)
    # El equivalente a los timestamps() de Laravel
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())