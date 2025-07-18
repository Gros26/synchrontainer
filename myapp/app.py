from flask import Flask, render_template, jsonify
import requests
import os 

app = Flask(__name__)

UID = os.environ['HOSTNAME']
NOMBRE_CONTENEDOR = os.environ.get("NOMBRE_CONTENEDOR", UID) 
#Ruta del archivo compartido entre contenedores
CONTENEDORES = "/usr/src/app/sync_files/registro/contenedores.txt"
RUTA_BASE = "/usr/src/app/sync_files/private/"


def registrar_contenedor(uid, nombre_contenedor, archivo):
  """Registra un contenedor si no está en el archivo."""
  if not os.path.exists(archivo):
      with open(archivo, "a") as f:
          f.write(f"{nombre_contenedor}: {uid}\n")
      return

  with open(archivo, "r+") as f:
      lineas = f.readlines()
      ya_registrado = any(linea.startswith(f"{nombre_contenedor}:") for linea in lineas)
      if not ya_registrado:
          f.write(f"{nombre_contenedor}: {uid}\n")


def listar_contenedores():
  """Devuelve un diccionario con todos los contenedores registrados."""
  contenedores = {}
  if os.path.exists(CONTENEDORES):
    with open(CONTENEDORES, "r") as f:
      for linea in f:
        if ':' in linea:
          clave, valor = linea.strip().split(":", 1)
          contenedores[clave.strip()] = valor.strip()
  return contenedores

@app.route('/')
def index():
  contenedores = listar_contenedores()
  return render_template("index.html", data=contenedores)




@app.route("/archivos/<nombre>")
def listar_archivos_contenedor(nombre):
  """Este es para que cada contenedor liste sus cosas y despues llamar a este endpoint"""
  carpeta = os.path.join(RUTA_BASE, nombre)

  if not os.path.exists(carpeta):
      return jsonify({"error": f"No se encontró la carpeta '{nombre}'"}), 404

  archivos = os.listdir(carpeta)
  return archivos


#Aqui llamamos al endpoint anterior para traer la lista 
@app.route('/storage/<uid>')
def listar_archivos_privados(uid):
    contenedores = listar_contenedores()
    nombre = None

    for llave, valor in contenedores.items():
      if valor == uid:
        nombre = llave
        break

    response = requests.get(f"http://{nombre}:5000/archivos/{nombre}")
    return response.json()


# Esta ruta permitira listar los archivos publicos de la red
@app.get('/public')
def listar_archivos_publicos():
  archivos = os.listdir("/usr/src/app/sync_files/public") # ruta dentro del contenedor
  print(archivos)
  return render_template("public.html", data=archivos)


@app.route('/despedirse')
def bye_world():
  return {
    'message': 'Adiós, mundo!!!'
  }

if __name__ == '__main__':
  # Registrar contenedor al iniciar
  registrar_contenedor(UID, NOMBRE_CONTENEDOR, CONTENEDORES)
  app.run(host='0.0.0.0',port=5000)