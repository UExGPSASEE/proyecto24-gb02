from sqlalchemy import desc, func
from sqlalchemy.orm import Session
from . import models, schemas
import requests

"""
Autor: Grupo GA01 - ASEE
Versión: 1.0
Descripción: Funciones CRUD para interactuar con la base de datos
"""
BASE_URL_CONTENIDOS = "http://127.0.0.1:8000"
BASE_URL_USUARIOS = "http://127.0.0.1:8001"

# Función para obtener los géneros de los contenidos del historial y "me gusta" de un usuario
def get_generos_usuario(db: Session, usuario_id: str):
    usuario = None
    generos_puntos = {}
    
    # Obtener el usuario
    response = requests.get(f"{BASE_URL_USUARIOS}/usuarios").json()
    for user in response:
        if user['id'] == usuario_id:
            usuario = user
    
    # Obtener el historial del usuario
    if usuario:
        historial_id = usuario['idHistorial']      

    if historial_id:
        historial = db.query(models.HistorialUsuario).filter(models.HistorialUsuario.idHistorial == historial_id).all()

    # Obtener los géneros de los contenidos en su historial
    if historial:
        for entrada in historial:
            contenido = requests.get(f"{BASE_URL_CONTENIDOS}/contenidos/{entrada.idContenido}").json()
            genero_id = contenido['idGenero']
            

            if genero_id:
                if genero_id not in generos_puntos:
                    generos_puntos[genero_id] = 1
                else:
                    generos_puntos[genero_id] += 1   
    
    # Obtener los contenidos que al usuario le gustan
    me_gusta = db.query(models.ListaMeGusta).filter(models.ListaMeGusta.idUsuario == usuario_id).all()
    if me_gusta:
        for entrada in me_gusta:
            contenido = requests.get(f"{BASE_URL_CONTENIDOS}/contenidos/{entrada.idContenido}").json()
            genero_id = contenido['idGenero']

            if genero_id:
                if genero_id not in generos_puntos:
                    generos_puntos[genero_id] = 1
                else:
                    generos_puntos[genero_id] += 1 

    # Ordenar los géneros por el número de repeticiones de mayor a menor
    generos_ordenados = sorted(generos_puntos.items(), key=lambda x: x[1], reverse=True)

    # Quedarse solo con los dos más repetidos para las recomendaciones
    top_2_generos = [genero for genero, _ in generos_ordenados[:2]]                          

    # Retornar los géneros
    return top_2_generos

# Función para obtener contenidos de los dos géneros favoritos de un usuario
def get_recomendaciones_usuario(db: Session, usuario_id: str):
    # Obtenemos los dos géneros favoritos del usuario
    generos = get_generos_usuario(db, usuario_id)
    
    # Obtenemos la lista de contenidos en función de esos géneros
    recomendaciones = []
    if generos:
        lista1 = requests.get(f"{BASE_URL_CONTENIDOS}/generos/{generos[0].id}").json()
        lista2 = requests.get(f"{BASE_URL_CONTENIDOS}/generos/{generos[1].id}").json()
        recomendaciones.extend(lista1)
        recomendaciones.extend(lista2)

    return recomendaciones    

#Función para dar "Me Gusta" a un contenido por un usuario
def dar_me_gusta(db: Session, idUsuario: str, idContenido: str):
    tupla_lista = models.ListaMeGusta(idUsuario=idUsuario,
                                      idContenido=idContenido)
    db.add(tupla_lista)
    db.commit()
    db.refresh(tupla_lista)
    return tupla_lista

#Función para quitar un contenido de la lista de "Me Gusta"
def quitar_me_gusta(db: Session, idUsuario: str, idContenido: str) -> bool:
    tupla_lista = db.query(models.ListaMeGusta).filter(models.ListaMeGusta.idUsuario == idUsuario, 
                                                       models.ListaMeGusta.idContenido == idContenido).first()
    if tupla_lista:
        db.delete(tupla_lista)
        db.commit()
        return True
    
    return False

#Función para valorar un contenido por un usuario
def valorar_contenido(db: Session, idUsuario: str, idContenido: str, valoracion: int):
    tupla_antigua = db.query(models.ValoracionUsuarioContenido).filter(
                                                                models.ValoracionUsuarioContenido.idUsuario == idUsuario,
                                                                models.ValoracionUsuarioContenido.idContenido == idContenido ).first()
    if not valoracion:
        return None
    #Se hace una llamada a la API de Contenidos 
    url = f"http://localhost:8000/contenidos/{idContenido}/valoracion"

    # Parámetros del cuerpo de la solicitud
    params = {
        "valoracion": valoracion
    }
    try:
        # Hacer la solicitud POST al endpoint
        response = requests.put(url, params=params)

        # Validar la respuesta
        if response.status_code == 200:
            print("Valoración añadida con éxito:", response.json())
        else:
            print("Error al añadir la valoración:", response.status_code, response.text)

    except requests.RequestException as e:
        print("Error al conectar con el servidor:", e)

    # Si existe ya una tupla con esa valoración, se edita
    if tupla_antigua:
        tupla_antigua.puntuacion = valoracion
        db.commit()
        db.refresh(tupla_antigua)
        return tupla_antigua
    # Si no existe, se crea una nueva
    tupla_nueva = models.ValoracionUsuarioContenido(idUsuario=idUsuario, idContenido=idContenido, puntuacion=valoracion)
    db.add(tupla_nueva)
    db.commit()
    db.refresh(tupla_nueva)
    return tupla_nueva    

# Función para añadir contenido al historial del usuario
def crear_entrada_historial(db: Session, usuario_id: str, contenido_id: str):
    # Obtener al usuario para consultar su id de historial
    usuario = None
    
    # Obtener el usuario
    response = requests.get(f"{BASE_URL_USUARIOS}/usuarios").json()
    for user in response:
        if user['id'] == usuario_id:
            usuario = user
    
    # Obtener el historial del usuario
    if usuario:
        historial_id = usuario['idHistorial']      

    # Crear una nueva entrada en el historial del usuario
    if historial_id:
        db_historial = models.HistorialUsuario(
            idHistorial=historial_id,
            idContenido=contenido_id
        )
        db.add(db_historial)
        db.commit()
        db.refresh(db_historial)
    return db_historial

# Función para obtener el historial del usuario
def get_historial_usuario(db: Session, usuario_id: str):
    # Obtener al usuario para consultar su id de historial
    usuario = None
    
    # Obtener el usuario
    response = requests.get(f"{BASE_URL_USUARIOS}/usuarios").json()
    for user in response:
        if user['id'] == usuario_id:
            usuario = user
    
    # Obtener el historial del usuario
    if usuario:
        historial_id = usuario['idHistorial'] 

    # Obtener todas las entradas del historial del usuario
    if historial_id:
        historial = db.query(models.HistorialUsuario).filter(models.HistorialUsuario.idHistorial == historial_id).all() 

    # Añadir a la lista a devolver todos los contenidos en el historiañ
    contenidos_historial = []
    if historial:
        for entrada in historial:
            contenido = requests.get(f"{BASE_URL_CONTENIDOS}/contenidos/{entrada.idContenido}").json()
            contenidos_historial.append(contenido)

    return contenidos_historial        

# Obtener los contenidos con más "me gusta"
def get_mas_me_gusta(db: Session, limite: int = 2):
    return (
        db.query(
            models.ListaMeGusta.idContenido.label("idContenido"),
            func.count(models.ListaMeGusta.idContenido).label("me_gusta_total")
        )
        .group_by(models.ListaMeGusta.idContenido)
        .order_by(desc("me_gusta_total"))
        .limit(limite)
        .all()
    )