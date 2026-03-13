from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

# Importamos desde la carpeta padre (la raíz del proyecto)
import models, schemas
from database import SessionLocal

# 1. Configuramos el Router (Este es tu "Controlador")
router = APIRouter(
    prefix="/ventas",
    tags=["Ventas"] # Esto agrupa las rutas bonito en la documentación de Swagger
)

# 2. Traemos nuestra dependencia de base de datos
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


# Guardar un venta
@router.post("/", response_model=schemas.VentaResponse)
def crear_venta(venta: schemas.VentaCreate, db: Session = Depends(get_db)):

    producto = db.query(models.Producto).filter(models.Producto.id == venta.producto_id).first()
    
    if producto is None:
        raise HTTPException(status_code=404, detail="Producto no encontrado")

    if producto.stock < venta.cantidad:
        raise HTTPException(
            status_code=400, 
            detail=f"No hay producto suficiente. Solo quedan {producto.stock} en stock."
        )
    
    producto.stock -= venta.cantidad
    # db.commit()

    # 1. Transformamos los datos validados al modelo de SQLAlchemy
    nueva_venta = models.Venta(**venta.model_dump())
    
    # 2. Lo preparamos para guardarlo
    db.add(nueva_venta)
    
    # 3. Hacemos el "save()" en la base de datos
    db.commit()
    
    # 4. Refrescamos para obtener el ID generado por Postgres
    db.refresh(nueva_venta)
    
    return nueva_venta
