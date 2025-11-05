from flask import Flask, render_template, request, jsonify, make_response, session, redirect, url_for
import mysql.connector
from flask_cors import CORS
import pusher
import bcrypt
import json
from functools import wraps # Necesario para el decorador de sesión

# --- Configuración de la Base de Datos (Adaptar a tus credenciales locales/Render) ---
db_config = {
    "host": "localhost", # Usar localhost o la IP de Render
    "database": "visage360_db",
    "user": "root",
    "password": ""
}

app = Flask(__name__)
# Permitir CORS para desarrollo local entre AngularJS y Flask
CORS(app) 

# Clave secreta para la gestión de sesiones de Flask (debe ser fuerte)
app.secret_key = "visage360_clave_secreta_fuerte_abc123"

# --- CONFIGURACIÓN DE PUSHER (Se mantiene la funcionalidad de notificaciones) ---
pusher_client = pusher.Pusher(
  app_id='2073459',
  key='196b5bf567ba56438181',
  secret='fc728ccb035c9171e6e7',
  cluster='us2',
  ssl=True
)

# =========================================================================
# FUNCIONES AUXILIARES
# =========================================================================

# Decorador para proteger rutas de la API (solo si usas sesiones de Flask)
def requiere_login_api(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        # En una arquitectura SPA/API RESTful, es mejor validar un token JWT
        # Por ahora, simulamos la validación simple de la sesión de Flask
        if "idUsuario" not in session:
            return jsonify({"message": "No autorizado. Inicie sesión."}), 401
        return f(*args, **kwargs)
    return decorated_function

# =========================================================================
# LOGIN (Adaptado para devolver JSON a AngularJS)
# =========================================================================

@app.route("/api/login", methods=["POST"])
@cross_origin() # Permite la llamada desde el front-end de AngularJS
def IniciarSesionAPI():
    # En AngularJS, los datos llegan como JSON, no como request.form
    data = request.get_json()
    usuario_ingresado = data.get("email") # Usamos 'email' según la tabla 'usuarios'
    contrasena_ingresada = data.get("password")

    if not usuario_ingresado or not contrasena_ingresada:
        return jsonify({"success": False, "message": "Datos de acceso incompletos"}), 400

    con = mysql.connector.connect(**db_config)
    cursor = con.cursor(dictionary=True)
    # MODIFICACIÓN: Buscar por 'email' y obtener 'id' y 'is_premium'
    cursor.execute("SELECT id, email, password, is_premium FROM usuarios WHERE email = %s", (usuario_ingresado,))
    registro_usuario = cursor.fetchone()
    con.close()

    if registro_usuario:
        # Nota: El campo 'password' debe ser 'password' en la tabla.
        hash_guardado = registro_usuario['password'].encode('utf-8')
        contrasena_ingresada_bytes = contrasena_ingresada.encode('utf-8')
        
        if bcrypt.checkpw(contrasena_ingresada_bytes, hash_guardado):
            # En la API, se devuelven los datos, AngularJS gestiona el estado (Patrón Singleton)
            return jsonify({
                "success": True, 
                "message": "Inicio de sesión exitoso.",
                "user": {
                    "id": registro_usuario["id"],
                    "email": registro_usuario["email"],
                    "is_premium": bool(registro_usuario["is_premium"]) # Asegura el valor booleano
                    # JWT Token real iría aquí
                }
            })

    return jsonify({"success": False, "message": "Correo o contraseña incorrectos"}), 401

# =========================================================================
# MÓDULO HISTORIAL DE ANALISIS (LECTURA - R del CRUD)
# =========================================================================

@app.route("/api/historial_analisis/<int:user_id>", methods=["GET"])
@cross_origin()
# En una aplicación real, aquí validaríamos un JWT token en el header
# @requiere_login_api
def getHistorialAnalisis(user_id):
    
    con = mysql.connector.connect(**db_config)
    cursor = con.cursor(dictionary=True)

    # MODIFICACIÓN: Traer todos los campos necesarios de la tabla analysis_history
    sql = """
    SELECT 
        id, user_id, analysis_date, tipo_analisis, status, 
        SUBSTRING(resultado_json, 1, 50) AS resumen_resultado
    FROM 
        analysis_history 
    WHERE 
        user_id = %s 
    ORDER BY 
        analysis_date DESC
    """
    cursor.execute(sql, (user_id,))
    registros = cursor.fetchall()
    
    cursor.close()
    con.close()
    
    # Devuelve el historial en formato JSON para AngularJS
    return jsonify({"success": True, "historial": registros})

# =========================================================================
# FUNCIÓN DE LECTURA DETALLADA (R adicional)
# =========================================================================

@app.route("/api/analisis/detalle/<int:analysis_id>", methods=["GET"])
@cross_origin()
def getDetalleAnalisis(analysis_id):
    con = mysql.connector.connect(**db_config)
    cursor = con.cursor(dictionary=True)

    # Se trae todo el JSON de resultado para mostrar el detalle
    sql = "SELECT resultado_json FROM analysis_history WHERE id = %s"
    cursor.execute(sql, (analysis_id,))
    registro = cursor.fetchone()
    con.close()
    
    if registro:
        # Se asume que resultado_json es un string JSON válido
        return jsonify({"success": True, "detalle": json.loads(registro['resultado_json'])})
    
    return jsonify({"success": False, "message": "Análisis no encontrado."}), 404

# =========================================================================
# SIMULACIÓN DE REGISTRO ASÍNCRONO (Para la futura C del CRUD)
# =========================================================================

@app.route("/api/analisis/iniciar", methods=["POST"])
@cross_origin()
def iniciarAnalisis():
    # ESTO SIMULA LA FUNCIÓN DE LA API QUE RECIBE LA IMAGEN Y DELEGA
    
    # Aquí iría la lógica de recepción de la imagen (request.files)
    
    # 1. Validación de Login y permisos
    # 2. Guardar la imagen en Render/S3
    # 3. Registrar el estado 'PENDING' en analysis_history
    # 4. Encolar la tarea en Redis (el 'Procesador de Tareas Asíncronas')

    # Simulamos el éxito al recibir la solicitud
    # En un proyecto real con Laravel/PHP, la API respondería inmediatamente:
    return jsonify({"success": True, "message": "Análisis en cola. Vuelva a consultar el historial en un momento."})


if __name__ == "__main__":
    app.run(debug=True)
