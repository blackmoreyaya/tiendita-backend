from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
# Importamos desde la carpeta padre (la raíz del proyecto)
import models, schemas
from database import SessionLocal
import os
from dotenv import load_dotenv
from google import genai
from twilio.rest import Client
# from apscheduler.schedulers.background import BackgroundScheduler


# Esto carga las variables de tu archivo .env
load_dotenv()

# Inicializamos el cliente de Gemini usando tu clave
cliente_ia = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))


# 1. Configuramos el Router (Este es tu "Controlador")
router = APIRouter(
    # prefix="/ventas",
    tags=["Agente"] # Esto agrupa las rutas bonito en la documentación de Swagger
)

# 2. Traemos nuestra dependencia de base de datos
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


@router.get("/test-ia/")
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


@router.get("/reporte-inventario/")
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




# Dependiendo de si usas router o app, pon @router.get o @app.get
@router.get("/reporte-bolis")
def enviar_reporte_arfily(db: Session = Depends(get_db)):
    
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
        Eres un asesor de negocios. Tu cliente es Arfily, dueño de una tiendita.
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

    
        print("¡Reporte enviado exitosamente a Arfily!")
    
            # Devolvemos un mensaje de éxito para saber que funcionó
        return {
            "status": "éxito", 
            "mensaje": "El reporte de inventario de bolis ha sido enviado por WhatsApp a Arfily. 🧊✨"
        }

    except Exception as e:
        print(f"❌ Error en la tarea automática: {str(e)}")
    finally:
        # 2. Es VITAL cerrar la conexión al terminar para no saturar Postgres
        db.close()



# Configuramos el temporizador
# scheduler = BackgroundScheduler()

# Para hacer pruebas, le diremos que se ejecute cada 15 SEGUNDOS (en vez de 15 días)
# scheduler.add_job(tarea_quincenal_inventario, 'interval', seconds=15)
# scheduler.add_job(tarea_quincenal_inventario, 'interval', days=15)

# Arrancamos el reloj
# scheduler.start()