from flask import Flask, render_template
import os 

app = Flask(__name__)

uid = os.environ['HOSTNAME']

@app.route('/')
def index():
  contenedores = ['contenedor1', 'contenedor2', 'contenedor3']
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
  app.run(host='0.0.0.0',port=5000)