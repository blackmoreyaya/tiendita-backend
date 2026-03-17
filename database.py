# from sqlalchemy import create_engine
# from sqlalchemy.orm import sessionmaker, declarative_base

# # Aquí pones tus credenciales de pgAdmin
# # Formato: postgresql://usuario:contraseña@localhost:5432/nombre_base_datos
# # Si tu usuario es "postgres" y tu contraseña es "1234", se vería así:
# URL_BASE_DATOS = "postgresql://postgres:12345678@localhost:5432/tienda"

# # El "engine" es el motor que maneja la comunicación con Postgres
# engine = create_engine(URL_BASE_DATOS)

# # La sesión es lo que usaremos para hacer consultas (guardar, buscar, etc.)
# SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# # Esto es como la clase "Model" base de Eloquent, de aquí heredarán nuestras tablas
# Base = declarative_base()

import os
from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base
from sqlalchemy.orm import sessionmaker
from dotenv import load_dotenv

# Esto carga las variables de tu archivo .env
load_dotenv() 

# Busca la URL en el .env. (En caso de que no exista, usa una base local de respaldo)
SQLALCHEMY_DATABASE_URL = os.getenv("DATABASE_URL")

# Nota: Si usabas SQLite antes, el engine llevaba 'connect_args={"check_same_thread": False}'. 
# Para PostgreSQL (Neon), eso se quita, así que el engine queda súper limpio:
engine = create_engine(SQLALCHEMY_DATABASE_URL)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()