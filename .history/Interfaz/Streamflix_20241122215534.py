from fastapi import FastAPI, Request, Form, HTTPException
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
import requests

# Comando de ejecución: uvicorn Streamflix:app --reload --host localhost --port 8003

#Creación de la API de interfaz
app = FastAPI()

BASE_URL_CONTENIDOS = "http://127.0.0.1:8000"
BASE_URL_USUARIOS = "http://127.0.0.1:8001"
BASE_URL_INTERACCIONES = "http://127.0.0.1:8002"

#Métodos auxiliares
def cargar_datos(user_id: str):
    """
    Obtiene y organiza los datos necesarios para la pantalla principal.
    """
    mensaje = None
    recomendaciones_response = requests.get(f"{BASE_URL_INTERACCIONES}/usuarios/{user_id}/recomendaciones")
    tendencias_response = requests.get(f"{BASE_URL_INTERACCIONES}/contenido/tendencias")
    historial_response = requests.get(f"{BASE_URL_INTERACCIONES}/usuarios/{user_id}/historial")
    generos_response = requests.get(f"{BASE_URL_CONTENIDOS}/generos")

    # Validar las respuestas
    if not (recomendaciones_response.ok and tendencias_response.ok and historial_response.ok and generos_response.ok):
        mensaje = "No se pudo recuperar la información de los microservicios."

    recomendaciones = recomendaciones_response.json() if recomendaciones_response.ok else []
    tendencias = tendencias_response.json() if tendencias_response.ok else []
    historial = historial_response.json() if historial_response.ok else []
    generos = generos_response.json() if generos_response.ok else []

    # Recuperar los contenidos por género
    generos_con_contenidos = []
    for genero in generos:
        contenidos_response = requests.get(f"{BASE_URL_CONTENIDOS}/generos/{genero['id']}/contenidos")
        if contenidos_response.ok:
            generos_con_contenidos.append({
                "nombre": genero["nombre"],
                "contenidos": contenidos_response.json()
            })

    return {
        "recomendaciones": recomendaciones,
        "tendencias": tendencias,
        "historial": historial,
        "generos_con_contenidos": generos_con_contenidos,
        "mensaje": mensaje,
    }



# Configuración de rutas estáticas para CSS
app.mount("/static", StaticFiles(directory="static"), name="static")

# Configuración de plantillas Jinja2
templates = Jinja2Templates(directory="templates")

# Endpoint para la página principal
@app.get("/", response_class=HTMLResponse)
async def index(request: Request):
    # Renderiza la página index.html y la devuelve al usuario
    return templates.TemplateResponse("index.html", {"request": request})

# Endpoint para hacer login
@app.post("/login")
async def login(request: Request, email: str = Form(...), password: str = Form(...)):
    # Enviar las credenciales al microservicio para verificar el login
    data = {"email": email, "password": password}
    response = requests.post(f"{BASE_URL_USUARIOS}/usuarios/login", json=data)
    
    if response.status_code != 200:
        raise HTTPException(status_code=400, detail="Credenciales inválidas")
    
    # Si las credenciales son correctas, obtenemos los datos del usuario
    user_data = response.json()
    user_id = user_data.get("id")

    datos = cargar_datos(user_id)
    
    # Redirigimos a la página principal
    return templates.TemplateResponse("pantalla_principal.html", {"request": request, "user_id": user_id, **datos})

# Endpoint para mostrar la página de registro
@app.get("/registro_usuario", response_class=HTMLResponse)
async def registro_usuario(request: Request):
    return templates.TemplateResponse("registro_usuario.html", {"request": request})

# Endpoint para obtener los planes de suscripción
@app.get("/planes_suscripcion")
async def obtener_planes():
    # Aquí haces una solicitud a tu microservicio que devuelve los planes
    response = requests.get(f"{BASE_URL_USUARIOS}/planes-suscripcion")
    if response.status_code != 200:
        raise HTTPException(status_code=500, detail="No se pudieron obtener los planes.")
    return response.json()

# Endpoint para registrar un nuevo usuario
@app.post("/registro")
async def registrar_usuario(request: Request, name: str = Form(...), email: str = Form(...), password: str = Form(...), language: str = Form(None), subscription_plan: str = Form(...)):
    # Aquí haces una solicitud para registrar al usuario en tu microservicio
    data = {
        "nombre": name,
        "email": email,
        "password": password,
        "idioma": language,
        "idPlanSuscripcion": subscription_plan
    }
    response = requests.post(f"{BASE_URL_USUARIOS}/usuarios/registro", json=data)
    if response.status_code != 200:
        raise HTTPException(status_code=500, detail="Error al registrar el usuario.")
    
    # Guardamos el id del usuario retornado
    user_data = response.json()
    user_id = user_data.get("id")

    datos = cargar_datos(user_id)
    
    # Podrías guardar el `user_id` para uso posterior si es necesario
    return templates.TemplateResponse("pantalla_principal.html", {"request": request, "user_id": user_id, **datos})

# Endpoint para mostrar los detalles de una película
@app.get("/detalles_pelicula/{idContenido}", response_class=HTMLResponse)
async def detalles_pelicula(request: Request, idContenido: str):
    # Solicita los detalles de la película al microservicio de contenidos
    contenido = requests.get(f"{BASE_URL_CONTENIDOS}/contenidos/{idContenido}")
    
    if contenido.status_code != 200:
        raise HTTPException(status_code=404, detail="No se encontraron los detalles de la película.")
      
    # Extrae los detalles de la película del JSON de la respuesta
    detalles_pelicula = contenido.json()

    #Extraer nombre del genero a partir del id
    genero = requests.get(f"{BASE_URL_CONTENIDOS}/generos/{detalles_pelicula["idGenero"]}")
    detalles_genero = genero.json()
    nombre_genero = detalles_genero["nombre"]

    #Extraer nombre del director a partir del id
    director = requests.get(f"{BASE_URL_CONTENIDOS}/directores/{detalles_pelicula["idDirector"]}")
    detalles_director = director.json()
    nombre_director = detalles_director["nombre"]

    #Cambiar los valores de ids por nombres
    detalles_pelicula["idGenero"] = nombre_genero
    detalles_pelicula["idDirector"] = nombre_director

    #Obtener el reparto
    reparto = requests.get(f"{BASE_URL_CONTENIDOS}/contenidos/{detalles_pelicula["id"]}/reparto")
    detalles_reparto = reparto.json()

    #Obtener los subtitulos
    subtitulos = requests.get(f"{BASE_URL_CONTENIDOS}/contenidos/{detalles_pelicula["idSubtitulosContenido"]}/subtitulos")
    detalles_subtitulos = subtitulos.json()
    
    #Obtener los doblajes
    doblajes = requests.get(f"{BASE_URL_CONTENIDOS}/contenidos/{detalles_pelicula["idDoblajeContenido"]}/doblajes")
    detalles_doblajes = doblajes.json()
    
    # Renderiza la plantilla detalles_pelicula.html con los datos de la película
    return templates.TemplateResponse("detalles_pelicula.html", {
        "request": request,
        "pelicula": detalles_pelicula,
        "reparto": detalles_reparto,
        "subtitulos": detalles_subtitulos,
        "doblajes": detalles_doblajes
    })


@app.get("/buscar", response_class=HTMLResponse)
async def buscar(request: Request, query: str, tipo: str):
    # Realizamos la búsqueda de contenidos o actores según el tipo
    if tipo == "contenido":
        response = requests.get(f"{BASE_URL_CONTENIDOS}/contenidos/{query}/buscar")
    elif tipo == "actor":
        response = requests.get(f"{BASE_URL_CONTENIDOS}/contenidos/{query}/actores")
    else:
        raise HTTPException(status_code=400, detail="Tipo de búsqueda no válido")

    # Si la respuesta no es exitosa (status_code != 200), manejamos el error pero no lanzamos una excepción
    if response.status_code != 200:
        resultados = []
        mensaje = "No se han encontrado resultados."
    else:
        resultados = response.json().get("resultados", [])
        # Si los resultados están vacíos, ponemos el mensaje de "No se han encontrado resultados"
        if not resultados:
            mensaje = "No se han encontrado resultados."
        else:
            mensaje = ""

    # Renderizamos la página con los resultados, ya sea vacíos o con el mensaje
    return templates.TemplateResponse(
        "resultados_busqueda.html",
        {
            "request": request,
            "resultados": resultados,
            "tipo": tipo,
            "query": query,
            "mensaje": mensaje
        }
    ) 
import logging
logging.basicConfig(level=logging.INFO)

@app.get("/pantalla_principal", response_class=HTMLResponse)
async def pantalla_principal(request: Request, user_id: str):
    recomendaciones_response = requests.get(f"{BASE_URL_INTERACCIONES}/usuarios/{user_id}/recomendaciones")
    tendencias_response = requests.get(f"{BASE_URL_INTERACCIONES}/contenido/tendencias")
    historial_response = requests.get(f"{BASE_URL_INTERACCIONES}/usuarios/{user_id}/historial")
    generos_response = requests.get(f"{BASE_URL_CONTENIDOS}/generos")

    if not (recomendaciones_response.ok 
        and tendencias_response.ok 
        and historial_response.ok 
        and generos_response.ok):
        mensaje = "No se han encontrado resultados." 

    generos = generos_response.json()
    logging.info(f"Géneros obtenidos: {generos}")

    generos_con_contenidos = []
    for genero in generos:
        contenidos_response = requests.get(f"{BASE_URL_CONTENIDOS}/generos/{genero['id']}/contenidos")
        if contenidos_response.ok:
            contenidos = contenidos_response.json()
            logging.info(f"Contenidos para el género {genero['nombre']}: {contenidos}")
            generos_con_contenidos.append({
                "nombre": genero['nombre'],
                "contenidos": contenidos
            })

    return templates.TemplateResponse(
        "pantalla_principal.html",
        {
            "request": request,
            "user_id": user_id,
            "recomendaciones": recomendaciones_response.json(),
            "tendencias": tendencias_response.json(),
            "historial": historial_response.json(),
            "generos_con_contenidos": generos_con_contenidos,
            "mensaje": mensaje
        }
    )


@app.get("/usuarios/{user_id}/perfil", response_class=HTMLResponse)
async def get_user_profile(request: Request, user_id: str):
    """Llama al endpoint /perfil para obtener el perfil de un usuario y lo renderiza en HTML"""
    response = requests.get(f"{BASE_URL_USUARIOS}/usuarios/{user_id}")
    me_gusta_response = requests.get(f"{BASE_URL_INTERACCIONES}/usuarios/{user_id}/me-gusta")
    
    if response.status_code == 200 and me_gusta_response.status_code == 200:
        # Obtiene los datos del perfil del usuario
        user_profile = response.json()
        
        # Obtiene la lista de contenidos "Me Gusta" y la convierte a una lista de objetos ContenidoMeGusta
        me_gusta_data = me_gusta_response.json()
        contenidos_me_gusta = [
            {
                'id': contenido['id'],
                'titulo': contenido['titulo'],
                'descripcion': contenido.get('descripcion', ''),
                'fechaLanzamiento': contenido['fechaLanzamiento'],
                'idGenero': contenido['idGenero'],
                'valoracionPromedio': contenido.get('valoracionPromedio', None),
                'idSubtitulosContenido': contenido.get('idSubtitulosContenido', None),
                'idDoblajeContenido': contenido.get('idDoblajeContenido', None)
            }
            for contenido in me_gusta_data
        ]

        # Renderiza la plantilla HTML con los datos del perfil y los "Me Gusta"
        return templates.TemplateResponse(
            "perfil.html",  # Plantilla HTML que renderizará los datos
            {
                "request": request,
                "user_id": user_id,
                "nombre": user_profile['nombre'],
                "email": user_profile['email'],
                "password": user_profile['password'],
                "me_gusta": contenidos_me_gusta  # Pasa la lista de contenidos "Me Gusta"
            }
        )
    else:
        # En caso de error, muestra un mensaje de error en la plantilla
        error_message = f"Error al obtener el perfil del usuario: {response.status_code}"
        return templates.TemplateResponse(
            "perfil.html",
            {
                "request": request,
                "error_message": error_message,
            }
        )