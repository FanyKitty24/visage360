# python.exe -m venv .venv
# cd .venv/Scripts
# activate.bat
# py -m ensurepip --upgrade
# pip install -r requirements.txt
# pip install bcrypt

from flask import Flask, render_template, request, jsonify, make_response, session, redirect, url_for
import mysql.connector
from flask_cors import CORS, cross_origin
import pusher
import bcrypt

# Configuración de la base de datos
db_config = {
    "host": "185.232.14.52",
    "database": "u760464709_23005019_bd",
    "user": "u760464709_23005019_usr",
    "password": "]0Pxl25["
}

app = Flask(__name__)
CORS(app)

# CONFIGURACIÓN DE PUSHER
pusher_client = pusher.Pusher(
    app_id='2048531',
    key='686124f7505c58418f23',
    secret='b5add38751c68986fc11',
    cluster='us2',
    ssl=True
)

app.secret_key = "pruebaLLaveSecreta_123"

def pusherAsistencias():
    pusher_client.trigger("canalAsistencias", "eventoAsistencias", {"message": "Nueva asistencia registrada."})
    return make_response(jsonify({}))

app.secret_key = "pruebaLLaveSecreta_123"

# =========================================================================
# LOGIN
# =========================================================================

@app.route("/")
def login():
    if "idUsuario" in session:
        return redirect(url_for("index"))
    return render_template("login.html")

@app.route("/IniciarSesion", methods=["POST"])
def IniciarSesion():
    usuario_ingresado = request.form.get("txtUsuario")
    contrasena_ingresada = request.form.get("txtContrasena")

    if not usuario_ingresado or not contrasena_ingresada:
        return "Datos incompletos", 400

    con = mysql.connector.connect(**db_config)
    cursor = con.cursor(dictionary=True)
    cursor.execute("SELECT idUsuario, username, password FROM usuarios WHERE username = %s", (usuario_ingresado,))
    registro_usuario = cursor.fetchone()
    con.close()

    if registro_usuario:
        hash_guardado = registro_usuario['password'].encode('utf-8')
        contrasena_ingresada_bytes = contrasena_ingresada.encode('utf-8')
        if bcrypt.checkpw(contrasena_ingresada_bytes, hash_guardado):
            session["idUsuario"] = registro_usuario["idUsuario"]
            session["username"] = registro_usuario["username"]
            return redirect(url_for("index"))

    return "Usuario o contraseña incorrectos", 401

@app.route("/index")
def index():
    if "idUsuario" not in session:
        return redirect(url_for("login"))
    return render_template("index.html")

@app.route("/cerrarSesion")
def cerrarSesion():
    session.clear()
    return redirect(url_for("login"))

# =========================================================================
# MÓDULO USUARIOS
# =========================================================================

@app.route("/empleados")
def empleados():
    # para poderla pasar al formulario.
    con = mysql.connector.connect(**db_config)
    cursor = con.cursor(dictionary=True)
    
    # Consulta para obtener todos los departamentos
    cursor.execute("SELECT idDepartamento, NombreDepartamento FROM departamento ORDER BY NombreDepartamento ASC")
    departamentos = cursor.fetchall()
    
    cursor.close()
    con.close()
    
    # Pasamos la lista de departamentos a la plantilla
    return render_template("empleados.html", departamentos=departamentos)
    
@app.route("/tbodyEmpleados")
def tbodyEmpleados():
    con = mysql.connector.connect(**db_config)
    cursor = con.cursor(dictionary=True)

    # MODIFICACIÓN: Se usa INNER JOIN para obtener el nombre del departamento.
    # Se selecciona E.* (todos los campos de empleados) y D.NombreDepartamento.
    sql = """
    SELECT 
        E.idEmpleado, 
        E.nombreEmpleado, 
        E.numero, 
        E.fechaIngreso, 
        E.idDepartamento,
        D.NombreDepartamento 
    FROM 
        empleados AS E
    INNER JOIN 
        departamento AS D ON E.idDepartamento = D.idDepartamento
    ORDER BY 
        E.idEmpleado DESC
    """
    cursor.execute(sql)
    registros = cursor.fetchall()
    
    cursor.close()
    con.close()
    
    return render_template("tbodyEmpleados.html", empleados=registros)

@app.route("/empleado", methods=["POST"])
def guardarEmpleado():
    con = mysql.connector.connect(**db_config)
    cursor = con.cursor()
    
    idEmpleado     = request.form.get("idEmpleado", "")
    nombreEmpleado = request.form["nombreEmpleado"]
    numero         = request.form["numero"]
    fechaIngreso   = request.form["fechaIngreso"]
    idDepartamento = request.form["idDepartamento"]

    if idEmpleado:
        sql = "UPDATE empleados SET nombreEmpleado = %s, numero = %s, fechaIngreso = %s, idDepartamento = %s WHERE idEmpleado = %s"
        val = (nombreEmpleado, numero, fechaIngreso, idDepartamento, idEmpleado)
    else:
        sql = "INSERT INTO empleados (nombreEmpleado, numero, fechaIngreso, idDepartamento) VALUES (%s, %s, %s, %s)"
        val = (nombreEmpleado, numero, fechaIngreso, idDepartamento)
    
    cursor.execute(sql, val)
    con.commit()

    cursor.close()
    con.close()
    
    return make_response(jsonify({}))

# =========================================================================
# MÓDULO HISTORIAL DE ANALISIS
# =========================================================================

@app.route("/historial_analisis")
def asistencias():
    return render_template("historial_analisis.html")

@app.route("/tbodyHistorialAnalisis")
def tbodyHistorialAnalisis():
    con = mysql.connector.connect(**db_config)
    cursor = con.cursor(dictionary=True)

    sql    = "SELECT id_analysis, user_id, analysis_date, image_url, tipo_analisis, resultado_json, status FROM analysis_history ORDER BY id_analysis DESC"
    cursor.execute(sql)
    registros = cursor.fetchall()

    cursor.close()
    con.close()
    
    return render_template("tbodyHistorialAnalisis.html", historial_analisis=registros)

@app.route("/historial_analisis", methods=["POST"])
def guardarHistorialAnalisis():
    con = mysql.connector.connect(**db_config)
    cursor = con.cursor()
    
    fecha      = request.form["fecha"]
    comentarios = request.form["comentarios"]
    
    sql    = "INSERT INTO asistencias (fecha, comentarios) VALUES (%s, %s)"
    val    = (fecha, comentarios)
    
    cursor.execute(sql, val)
    con.commit()

    cursor.close()
    con.close()

    pusherAsistencias()
    return make_response(jsonify({}))

