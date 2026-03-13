from fastapi import FastAPI, Depends, HTTPException # <--- Agregamos Depends
from sqlalchemy.orm import Session # <--- Agregamos Session
from database import engine, SessionLocal, Base # <--- Traemos SessionLocal
import models
import schemas # <--- Importamos nuestros nuevos esquemas
import os
from dotenv import load_dotenv
from google import genai
from apscheduler.schedulers.background import BackgroundScheduler
from twilio.rest import Client


# Esto carga las variables de tu archivo .env
load_dotenv()

# Inicializamos el cliente de Gemini usando tu clave
cliente_ia = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))

# Esto crea las tablas en la base de datos si no existen (como php artisan migrate)
Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="Agente de Inventario API",
    description="Backend para el sistema de predicción de la tiendita",
    version="1.0.0"
)

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

@app.get("/")
def leer_raiz():
    return {"mensaje": "¡El cerebro de la tiendita está vivo!"}

# Guardar un producto
@app.post("/productos/", response_model=schemas.ProductoResponse)
def crear_producto(producto: schemas.ProductoCreate, db: Session = Depends(get_db)):
    # 1. Transformamos los datos validados al modelo de SQLAlchemy
    nuevo_producto = models.Producto(**producto.model_dump())
    
    # 2. Lo preparamos para guardarlo
    db.add(nuevo_producto)
    
    # 3. Hacemos el "save()" en la base de datos
    db.commit()
    
    # 4. Refrescamos para obtener el ID generado por Postgres
    db.refresh(nuevo_producto)
    
    return nuevo_producto

# Traer TODOS los productos
@app.get("/productos/", response_model=list[schemas.ProductoResponse])
def leer_productos(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    # Esto es como Producto::skip($skip)->take($limit)->get();
    productos = db.query(models.Producto).offset(skip).limit(limit).all()
    return productos

# Traer UN SOLO producto por su ID
@app.get("/productos/{producto_id}", response_model=schemas.ProductoResponse)
def leer_producto(producto_id: str, db: Session = Depends(get_db)):
    # Esto es como Producto::find($id);
    producto = db.query(models.Producto).filter(models.Producto.id == producto_id).first()
    
    # Esto es el equivalente a findOrFail()
    if producto is None:
        raise HTTPException(status_code=404, detail="Producto no encontrado")
        
    return producto

# Actualizar un producto
@app.put("/productos/{producto_id}", response_model=schemas.ProductoResponse)
def actualizar_producto(producto_id: str, producto_actualizado: schemas.ProductoCreate, db: Session = Depends(get_db)):
    producto = db.query(models.Producto).filter(models.Producto.id == producto_id).first()
    
    if producto is None:
        raise HTTPException(status_code=404, detail="Producto no encontrado")
    
    # Actualizamos los campos uno por uno
    for key, value in producto_actualizado.model_dump().items():
        setattr(producto, key, value)
    
    db.commit()
    db.refresh(producto) # Refrescamos para obtener la nueva fecha de updated_at
    return producto

# Eliminación lógica de un producto
@app.delete("/productos/{producto_id}")
def eliminar_producto(producto_id: str, db: Session = Depends(get_db)):
    producto = db.query(models.Producto).filter(models.Producto.id == producto_id).first()
    
    if producto is None:
        raise HTTPException(status_code=404, detail="Producto no encontrado")
    
    # En lugar de borrarlo, lo desactivamos (Soft Delete)
    producto.status = False
    db.commit()
    
    return {"mensaje": f"El producto {producto.nombre} ha sido desactivado correctamente."}


# Guardar un venta
@app.post("/ventas/", response_model=schemas.VentaResponse)
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


@app.get("/test-ia/")
def probar_inteligencia_artificial():
    try:
        # Le mandamos un prompt sencillo a Gemini 2.5 Flash (el modelo más rápido y barato)
        respuesta = cliente_ia.models.generate_content(
            model='gemini-2.5-flash',
            contents='Eres el asistente de una tiendita. Dime una frase corta y motivadora sobre vender papas fritas.'
        )
        
        return {"mensaje_de_gemini": respuesta.text}
    
    except Exception as e:
        return {"error": str(e)}


@app.get("/reporte-inventario/")
def generar_reporte_inventario(db: Session = Depends(get_db)):
    # 1. Sacamos todos los productos activos de la base de datos
    productos = db.query(models.Producto).filter(models.Producto.status == True).all()
    
    if not productos:
        return {"mensaje": "No hay productos registrados para analizar."}

    # 2. Traducimos los datos de Postgres a un texto que la IA entienda
    datos_inventario = "Inventario actual de la tiendita:\n"
    for p in productos:
        datos_inventario += f"- {p.nombre}: Quedan {p.stock} unidades. (Precio: ${p.precio})\n"

    # 3. El "Prompt Engineering" (Aquí está el verdadero secreto del proyecto)
    prompt = f"""
    Eres un asesor de negocios inteligente y amigable. 
    Tu cliente es Ángel, el dueño de una tiendita de abarrotes.
    
    Aquí tienes los datos de su inventario actual:
    {datos_inventario}
    
    Tu tarea:
    Redacta un mensaje corto y directo para enviárselo a Ángel por WhatsApp.
    1. Salúdalo por su nombre.
    2. Dile qué productos urgen pedir (si tienen menos de 10 unidades es alerta roja).
    3. Dile cuáles NO debe pedir porque tiene stock de sobra (más de 20 unidades).
    4. Explícale brevemente cómo esta sugerencia le ahorra dinero o evita mermas.
    
    Usa emojis para que sea fácil de leer en el celular. No inventes datos, usa solo el inventario provisto.
    """

    # 4. Se lo enviamos a Gemini
    try:
        respuesta = cliente_ia.models.generate_content(
            model='gemini-2.5-flash',
            contents=prompt
        )
        return {"mensaje_whatsapp": respuesta.text}
        
    except Exception as e:
        return {"error": str(e)}
    

def tarea_quincenal_inventario():
    print("⏳ Iniciando análisis de inventario automático...")
    
    # 1. Abrimos nuestra propia conexión a la BD manualmente
    db = SessionLocal()
    try:
        productos = db.query(models.Producto).filter(models.Producto.status == True).all()
        
        if not productos:
            print("❌ No hay productos para analizar.")
            return

        datos_inventario = "Inventario actual:\n"
        for p in productos:
            datos_inventario += f"- {p.nombre}: Quedan {p.stock} unidades.\n"

        prompt = f"""
        Eres un asesor de negocios. Tu cliente es Ángel, dueño de una tiendita.
        Inventario: {datos_inventario}
        Redacta un mensaje corto para WhatsApp diciéndole qué pedir con urgencia (menos de 10) y qué NO pedir (más de 20). Usa emojis.
        """

        respuesta = cliente_ia.models.generate_content(
            model='gemini-2.5-flash',
            contents=prompt
        )
        
        print("\n✅ ¡REPORTE GENERADO CON ÉXITO!\n")
        print(respuesta.text)
        print("\n--------------------------------------------------\n")
        
        # AQUÍ EN EL FUTURO AGREGAREMOS EL CÓDIGO PARA ENVIAR EL WHATSAPP
        # ... tu código anterior que generaba la respuesta de Gemini ...
        
        texto_whatsapp = respuesta.text
        
        # 5. Conectamos con Twilio
        cliente_twilio = Client(os.getenv("TWILIO_ACCOUNT_SID"), os.getenv("TWILIO_AUTH_TOKEN"))
        
        # 6. Disparamos el mensaje
        mensaje = cliente_twilio.messages.create(
            from_=os.getenv("TWILIO_PHONE_NUMBER"),
            body=texto_whatsapp,
            to=os.getenv("MI_NUMERO_CELULAR")
        )
        
        print(f"\n✅ ¡WHATSAPP ENVIADO CON ÉXITO! ID: {mensaje.sid}\n")
        
    except Exception as e:
        print(f"❌ Error en la tarea automática: {str(e)}")
    finally:
        # 2. Es VITAL cerrar la conexión al terminar para no saturar Postgres
        db.close()


# Configuramos el temporizador
scheduler = BackgroundScheduler()

# Para hacer pruebas, le diremos que se ejecute cada 15 SEGUNDOS (en vez de 15 días)
# scheduler.add_job(tarea_quincenal_inventario, 'interval', seconds=15)
scheduler.add_job(tarea_quincenal_inventario, 'interval', days=15)

# Arrancamos el reloj
scheduler.start()