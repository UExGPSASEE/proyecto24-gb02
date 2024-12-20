from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from . import models, crud 
import os 

"""
Autor: Grupo GA01 - ASEE
Versión: 1.0
Descripción: Conexión a la base de datos usuarios.db y creación de sesión

"""

# URL de la base de datos (SQLite en este caso)
# Acceso antes de realizar los cambios de DOCKER!!!! SQLALCHEMY_DATABASE_URL = "sqlite:///./Microservicio_Usuarios/usuarios.db"

#Acceso a la base de datos tras realizar los cambios con Docker
DB_PATH = os.getenv("DB_PATH", "/app/usuarios.db")  # /app es el directorio de trabajo del contenedor
SQLALCHEMY_DATABASE_URL = f"sqlite:///{DB_PATH}"

# Crear el motor para interactuar con la base de datos
engine = create_engine(
    SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False}
)

# Crear una fábrica de sesiones para hacer queries
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Base para los modelos de SQLAlchemy
Base = declarative_base()

# Dependencia para obtener una sesión de base de datos
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# Función para inicializar la base de datos
def initialize_database():
    if not os.path.exists(DB_PATH):
        # Crea las tablas si no existen
        Base.metadata.create_all(bind=engine)
        print("Base de datos creada y tablas inicializadas.")

        # Insertar valores iniciales
        db = SessionLocal()
        try:
            planesExistentes = db.query(models.PlanSuscripcion).count()
            if planesExistentes == 0:
                nuevo_plan = models.PlanSuscripcion(id="P1", nombre="Plan Básico", precioMensual=5.49, numeroDispositivos=1)
                db.add(nuevo_plan)
                nuevo_plan = models.PlanSuscripcion(id="P2", nombre="Plan Medio", precioMensual=9.99, numeroDispositivos=2)
                db.add(nuevo_plan)
                nuevo_plan = models.PlanSuscripcion(id="P3", nombre="Plan Premium", precioMensual=12.99, numeroDispositivos=4)
                db.add(nuevo_plan)           
            
            db.commit()
            print("Valores iniciales insertados (Planes de suscripción).")
        finally:
            db.close()
