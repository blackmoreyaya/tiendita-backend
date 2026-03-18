from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

# Importamos desde la carpeta padre (la raíz del proyecto)
import models, schemas
from database import SessionLocal

# 1. Configuramos el Router (Este es tu "Controlador")
router = APIRouter(
    prefix="/productos",
    tags=["Productos"] # Esto agrupa las rutas bonito en la documentación de Swagger
)

# 2. Traemos nuestra dependencia de base de datos
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# 3. Pegamos aquí tus rutas de productos. ¡Ojo! Cambiamos @app por @router
# Como el prefijo ya es "/productos", la ruta raíz queda solo como "/"
@router.post("/", response_model=schemas.ProductoResponse)
def crear_producto(producto: schemas.ProductoCreate, db: Session = Depends(get_db)):
    nuevo_producto = models.Producto(**producto.model_dump())
    db.add(nuevo_producto)
    db.commit()
    db.refresh(nuevo_producto)
    return nuevo_producto

@router.get("/", response_model=list[schemas.ProductoResponse])
def leer_productos(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    productos = db.query(models.Producto).offset(skip).limit(limit).all()
    return productos

@router.get("/{producto_id}", response_model=schemas.ProductoResponse)
def leer_producto(producto_id: str, db: Session = Depends(get_db)):
    producto = db.query(models.Producto).filter(models.Producto.id == producto_id).first()
    if producto is None:
        raise HTTPException(status_code=404, detail="Producto no encontrado")
    return producto

@router.put("/{producto_id}", response_model=schemas.ProductoResponse)
def actualizar_producto(producto_id: str, producto_actualizado: schemas.ProductoCreate, db: Session = Depends(get_db)):
    producto = db.query(models.Producto).filter(models.Producto.id == producto_id).first()
    if producto is None:
        raise HTTPException(status_code=404, detail="Producto no encontrado")
    
    for key, value in producto_actualizado.model_dump().items():
        setattr(producto, key, value)
    
    db.commit()
    db.refresh(producto)
    return producto


@router.patch("/{producto_id}", response_model=schemas.ProductoResponse)
def actualizar_producto(producto_id: str, producto_actualizado: schemas.ProductoUpdate, db: Session = Depends(get_db)):
    producto = db.query(models.Producto).filter(models.Producto.id == producto_id).first()
    if producto is None:
        raise HTTPException(status_code=404, detail="Producto no encontrado")
    
    # La magia: exclude_unset=True solo toma los campos que el frontend envió
    datos_nuevos = producto_actualizado.model_dump(exclude_unset=True)
    
    for key, value in datos_nuevos.items():
        setattr(producto, key, value)
    
    db.commit()
    db.refresh(producto)
    return producto


@router.delete("/{producto_id}")
def eliminar_producto(producto_id: str, db: Session = Depends(get_db)):
    producto = db.query(models.Producto).filter(models.Producto.id == producto_id).first()
    if producto is None:
        raise HTTPException(status_code=404, detail="Producto no encontrado")
    
    producto.status = False
    db.commit()
    return {"mensaje": f"El producto {producto.nombre} ha sido desactivado correctamente."}