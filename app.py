from flask import Flask, render_template, request, jsonify, make_response, session, redirect, url_for
import mysql.connector
from flask_cors import CORS, cross_origin
import bcrypt
import json
from functools import wraps 

# --- Configuración de la Base de Datos (Adaptar a tus credenciales locales/Render) ---
db_config = {
    "host": "185.232.14.52", 
    "database": "a264133_visage360_db",
    "user": "185.232.14.52",
    "password": "24002200"
}

app = Flask(__name__)
# Permitir CORS para desarrollo local entre AngularJS y Flask
CORS(app) 

# Clave secreta para la gestión de sesiones de Flask (debe ser fuerte)
app.secret_key = "visage360_clave_secreta_fuerte_abc123"



# =========================================================================
# FUNCIONES AUXILIARES
# =========================================================================

# Decorador para proteger rutas de la API (generalmente no necesario en RESTful con JWT)
def requiere_login_api(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if "idUsuario" not in session:
            return jsonify({"message": "No autorizado. Inicie sesión."}), 401
        return f(*args, **kwargs)
    return decorated_function

# =========================================================================
# LOGIN (Lectura de la tabla usuarios)
# =========================================================================

@app.route("/api/login", methods=["POST"])
@cross_origin()
def IniciarSesionAPI():
    data = request.get_json()
    usuario_ingresado = data.get("email")
    contrasena_ingresada = data.get("password")

    if not usuario_ingresado or not contrasena_ingresada:
        return jsonify({"success": False, "message": "Datos de acceso incompletos"}), 400

    con = mysql.connector.connect(**db_config)
    cursor = con.cursor(dictionary=True)
    cursor.execute("SELECT id, email, password, is_premium FROM usuarios WHERE email = %s", (usuario_ingresado,))
    registro_usuario = cursor.fetchone()
    con.close()

    if registro_usuario:
        hash_guardado = registro_usuario['password'].encode('utf-8')
        contrasena_ingresada_bytes = contrasena_ingresada.encode('utf-8')
        
        if bcrypt.checkpw(contrasena_ingresada_bytes, hash_guardado):
            # Respuesta JSON para el Patrón Singleton en AngularJS
            return jsonify({
                "success": True, 
                "message": "Inicio de sesión exitoso.",
                "user": {
                    "id": registro_usuario["id"],
                    "email": registro_usuario["email"],
                    "is_premium": bool(registro_usuario["is_premium"]) 
                }
            })

    return jsonify({"success": False, "message": "Correo o contraseña incorrectos"}), 401

# =========================================================================
# MÓDULO HISTORIAL DE ANALISIS (LECTURA - R del CRUD)
# =========================================================================

@app.route("/api/historial_analisis/<int:user_id>", methods=["GET"])
@cross_origin()
# @requiere_login_api # Se comenta, pero se usaría en producción
def getHistorialAnalisis(user_id):
    
    con = mysql.connector.connect(**db_config)
    cursor = con.cursor(dictionary=True)

    sql = """
    SELECT 
        id_analysis, user_id, analysis_date, tipo_analisis, status, 
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

    sql = "SELECT resultado_json FROM analysis_history WHERE id_analysis = %s"
    cursor.execute(sql, (analysis_id,))
    registro = cursor.fetchone()
    con.close()
    
    if registro:
        try:
            detalle_json = json.loads(registro['resultado_json'])
        except json.JSONDecodeError:
            return jsonify({"success": False, "message": "Error en el formato JSON de la base de datos."}), 500

        return jsonify({"success": True, "detalle": detalle_json})
    
    return jsonify({"success": False, "message": "Análisis no encontrado."}), 404

# =========================================================================
# SIMULACIÓN DE REGISTRO ASÍNCRONO (Para la futura C del CRUD)
# =========================================================================

@app.route("/api/analisis/iniciar", methods=["POST"])
@cross_origin()
def iniciarAnalisis():
    # Esta ruta actúa como el punto de contacto entre la SPA y el Procesador de Tareas Asíncronas
    
    # Lógica de encolamiento y registro de PENDING
    
    return jsonify({"success": True, "message": "Análisis en cola. Vuelva a consultar el historial en un momento."})


if __name__ == "__main__":
    app.run(debug=True)
