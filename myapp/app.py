from flask import Flask, render_template
import os 

app = Flask(__name__)

@app.route('/')
def hello_world():
  # return {
  #   'message': 'hola, Mundo!!!'
  # }
  return render_template("index.html")

# Esta ruta listara todos los archivos del contenedor <uid>
@app.route('/storage/<uid>')
def listar_archivos_contenedor(uid):
  return "Aqui iria la template"


# Esta ruta permitira listar los archivos publicos de la red
@app.route('/public/')
def listar_archivos_publicos():
  if os.path.exists("/usr/src/app/sync_files/public"):
    print(f"La ruta '{"/usr/src/app/sync_files/public"}' existe.")
  else:
    print(f"La ruta '{"/usr/src/app/sync_files/public"}' no existe.")
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