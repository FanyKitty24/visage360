from flask import Flask, render_template, request, jsonify, make_response, session, redirect, url_for
import mysql.connector
from flask_cors import CORS, cross_origin
import bcrypt
import json
from functools import wraps 

# --- Configuración de la Base de Datos (RENDER DEBE USAR VARIABLES DE ENTORNO) ---
db_config = {
    "host": "185.232.14.52", # Usar os.environ.get('DB_HOST') en Render
    "database": "a264133_visage360_db",
    "user": "185.232.14.52",
    "password": "24002200"
}

app = Flask(__name__)
CORS(app) 

app.secret_key = "visage360_clave_secreta_fuerte_abc123"


# =========================================================================
# RUTAS DE VISTAS ESTÁTICAS (SPA ENTRY POINT)
# ESTO RESUELVE EL ERROR "NOT FOUND" EN RENDER
# =========================================================================

@app.route("/")
def render_app():
    # Sirve el archivo principal index.html (debe estar en la carpeta 'templates/')
    return render_template("index.html")

@app.route("/vistas/<path:filename>")
def serve_vistas(filename):
    # Sirve las vistas parciales solicitadas por AngularJS
    # ej: templateUrl: "/vistas/login.html"
    return render_template(f"vistas/{filename}")


# =========================================================================
# FUNCIONES AUXILIARES
# =========================================================================

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

@app.route("/IniciarSesion", methods=["POST"])
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

@app.route("/historial_analisis/<int:user_id>", methods=["GET"])
@cross_origin()
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
    
    return jsonify({"success": True, "historial": registros})

# =========================================================================
# FUNCIÓN DE LECTURA DETALLADA (R adicional)
# =========================================================================

@app.route("/analisis/detalle/<int:analysis_id>", methods=["GET"])
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

@app.route("/analisis/iniciar", methods=["POST"])
@cross_origin()
def iniciarAnalisis():
    # Simula la lógica de encolamiento y registro de PENDING
    return jsonify({"success": True, "message": "Análisis en cola. Vuelva a consultar el historial en un momento."})


if __name__ == "__main__":
    app.run(debug=True)
