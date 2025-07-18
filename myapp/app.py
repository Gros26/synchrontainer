from flask import Flask, render_template, jsonify
import os 

app = Flask(__name__)


UID = os.environ['HOSTNAME']

NOMBRE_CONTENEDOR = os.environ.get("NOMBRE_CONTENEDOR", UID) 

# Ruta del archivo compartido entre contenedores
CONTENEDORES = "/usr/src/app/sync_files/contenedores.txt"


def registrar_nodo(uid: str, nombre_contenedor: str, archivo: str):
  """Registra un nodo si no está en el archivo."""
  if not os.path.exists(archivo):
      with open(archivo, "w") as f:
          f.write(f"{nombre_contenedor}: {uid}\n")
      return

  with open(archivo, "r+") as f:
      lineas = f.readlines()
      ya_registrado = any(linea.startswith(f"{uid}:") for linea in lineas)
      if not ya_registrado:
          f.write(f"{nombre_contenedor}: {uid}\n")



def listar_nodos():
  """Devuelve un diccionario con todos los nodos registrados."""
  nodos = {}
  if os.path.exists(CONTENEDORES):
      with open(CONTENEDORES, "r") as f:
          for linea in f:
              if ':' in linea:
                  clave, valor = linea.strip().split(":", 1)
                  nodos[clave.strip()] = valor.strip()
  return nodos

@app.route('/')
def index():
  contenedores = listar_nodos()
  return render_template("index.html", data=contenedores)


# Esta ruta listara todos los archivos del contenedor <uid>
@app.get('/storage/<uid>')
def listar_archivos_contenedor(uid):
  return render_template("public.html", data=uid)


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
  # Registrar nodo al iniciar
  registrar_nodo(UID, NOMBRE_CONTENEDOR, CONTENEDORES)

  app.run(host='0.0.0.0',port=5000)