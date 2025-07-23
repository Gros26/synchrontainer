from flask import Flask, render_template, jsonify, request, send_from_directory, redirect, url_for, flash
import requests
import os 
from werkzeug.utils import secure_filename

app = Flask(__name__, static_url_path='/static')  # Sirve archivos estáticos desde /static

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
        # Si la petición espera JSON, devolvemos error JSON
        if request.accept_mimetypes['application/json'] >= request.accept_mimetypes['text/html']:
            return jsonify({"error": f"No se encontró la carpeta '{nombre}'"}), 404
        # Si espera HTML, renderizamos una plantilla de error
        return render_template("archivos_contenedor.html", nombre=nombre, archivos=None, error=f"No se encontró la carpeta '{nombre}'")

    archivos = os.listdir(carpeta)
    # Si la petición espera JSON, devolvemos JSON
    if request.accept_mimetypes['application/json'] >= request.accept_mimetypes['text/html']:
        return jsonify(archivos)
    # Si espera HTML, renderizamos la plantilla
    return render_template("archivos_contenedor.html", nombre=nombre, archivos=archivos, error=None)


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
    archivos = response.json() if response.status_code == 200 else []
    # Si la petición espera JSON, devolvemos JSON
    if request.accept_mimetypes['application/json'] >= request.accept_mimetypes['text/html']:
        return jsonify(archivos)
    # Si espera HTML, renderizamos la plantilla
    return render_template("storage_uid.html", nombre=nombre, archivos=archivos, error=None)


# Esta ruta permitira listar los archivos publicos de la red
@app.get('/public')
def listar_archivos_publicos():
  archivos = os.listdir("/usr/src/app/sync_files/public") # ruta dentro del contenedor
  print(archivos)
  return render_template("public.html", data=archivos)


@app.route('/download/<filename>')
def descargar_archivo_publico(filename):
    """Permite descargar un archivo público por su nombre."""
    return send_from_directory(PUBLIC_DIR, filename, as_attachment=True)


@app.route('/upload/<uid>/<filename>', methods=['GET', 'POST'])
def upload_archivo_privado(uid, filename):
    """Permite subir un archivo a la carpeta privada del contenedor <uid>."""
    contenedores = listar_contenedores()
    nombre = None
    for llave, valor in contenedores.items():
        if valor == uid:
            nombre = llave
            break
    if not nombre:
        return f"No se encontró el contenedor con UID {uid}", 404
    carpeta_destino = os.path.join(PRIVATE_DIR, nombre)
    os.makedirs(carpeta_destino, exist_ok=True)
    if request.method == 'POST':
        if 'file' not in request.files:
            flash('No se envió ningún archivo')
            return redirect(request.url)
        file = request.files['file']
        if file.filename == '':
            flash('No se seleccionó ningún archivo')
            return redirect(request.url)
        filename_seguro = secure_filename(filename)
        file.save(os.path.join(carpeta_destino, filename_seguro))
        return redirect(url_for('listar_archivos_privados', uid=uid))
    # Si es GET, mostrar formulario simple
    return '''
    <!doctype html>
    <title>Subir archivo privado</title>
    <h1>Subir archivo a contenedor {}</h1>
    <form method=post enctype=multipart/form-data>
      <input type=file name=file>
      <input type=submit value=Subir>
    </form>
    '''.format(nombre)


@app.route('/upload/public/<filename>', methods=['GET', 'POST'])
def upload_archivo_publico(filename):
    """Permite subir un archivo a la carpeta pública."""
    if request.method == 'POST':
        if 'file' not in request.files:
            flash('No se envió ningún archivo')
            return redirect(request.url)
        file = request.files['file']
        if file.filename == '':
            flash('No se seleccionó ningún archivo')
            return redirect(request.url)
        filename_seguro = secure_filename(filename)
        file.save(os.path.join(PUBLIC_DIR, filename_seguro))
        return redirect(url_for('listar_archivos_publicos'))
    # Si es GET, mostrar formulario simple
    return '''
    <!doctype html>
    <title>Subir archivo público</title>
    <h1>Subir archivo a la carpeta pública</h1>
    <form method=post enctype=multipart/form-data>
      <input type=file name=file>
      <input type=submit value=Subir>
    </form>
    '''


@app.route('/despedirse')
def bye_world():
    # Si la petición espera JSON, devolvemos JSON
    if request.accept_mimetypes['application/json'] >= request.accept_mimetypes['text/html']:
        return {
            'message': 'Adiós, mundo!!!'
        }
    # Si espera HTML, renderizamos la plantilla
    return render_template("despedirse.html")

# Asegurarse de que existan las carpetas necesarias al iniciar el contenedor
SYNC_FILES = "/usr/src/app/sync_files"
PUBLIC_DIR = os.path.join(SYNC_FILES, "public")
PRIVATE_DIR = os.path.join(SYNC_FILES, "private")
REGISTRO_DIR = os.path.join(SYNC_FILES, "registro")

os.makedirs(PUBLIC_DIR, exist_ok=True)
os.makedirs(PRIVATE_DIR, exist_ok=True)
os.makedirs(REGISTRO_DIR, exist_ok=True)

@app.route('/download/private/<uid>/<filename>')
def descargar_archivo_privado(uid, filename):
    """Permite descargar un archivo privado de un contenedor por su UID y nombre de archivo."""
    contenedores = listar_contenedores()
    nombre = None
    for llave, valor in contenedores.items():
        if valor == uid:
            nombre = llave
            break
    if not nombre:
        return f"No se encontró el contenedor con UID {uid}", 404
    carpeta_origen = os.path.join(PRIVATE_DIR, nombre)
    return send_from_directory(carpeta_origen, filename, as_attachment=True)

if __name__ == '__main__':
  # Registrar contenedor al iniciar
  registrar_contenedor(UID, NOMBRE_CONTENEDOR, CONTENEDORES)
  app.run(host='0.0.0.0',port=5000)