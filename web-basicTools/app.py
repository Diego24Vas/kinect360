"""
Servidor Web Flask para la interfaz de Kinect 360.
Expone la transmisión de video en tiempo real y endpoints de configuración.
"""

import os
import sys
from flask import Flask, render_template, Response, request, jsonify

# Configuración de rutas para imports robustos
DIR_ACTUAL = os.path.dirname(os.path.abspath(__file__))
DIRECTORIO_RAIZ = os.path.abspath(os.path.join(DIR_ACTUAL, ".."))
DIR_PYTHON_TOOLS = os.path.join(DIRECTORIO_RAIZ, "python-basicTools")

for ruta in (DIR_ACTUAL, DIRECTORIO_RAIZ, DIR_PYTHON_TOOLS):
    if ruta not in sys.path:
        sys.path.insert(0, ruta)

try:
    from control_kinect import GestorFlujoVideo, ControladorMotor
except ImportError:
    try:
        from .control_kinect import GestorFlujoVideo, ControladorMotor
    except ImportError:
        from camera_stream import GestorFlujoVideo
        from motor_controller import ControladorMotor

# Inicializar aplicación Flask
app = Flask(
    __name__,
    template_folder=os.path.join(os.path.dirname(__file__), "templates"),
    static_folder=os.path.join(os.path.dirname(__file__), "static")
)

# Instancias desacopladas: Video y Motor
gestor_video = GestorFlujoVideo()
controlador_motor = ControladorMotor()

@app.route("/")
def index():
    """Ruta principal: Renderiza la interfaz en una sola pantalla."""
    estado = gestor_video.obtener_estado()
    estado["angulo_motor"] = controlador_motor.obtener_angulo()
    return render_template("index.html", estado=estado)

@app.route("/video_feed")
def video_feed():
    """Ruta de transmisión MJPEG para la etiqueta <img> del navegador."""
    return Response(
        gestor_video.generar_mjpeg(),
        mimetype="multipart/x-mixed-replace; boundary=frame"
    )

@app.route("/api/state", methods=["GET"])
def get_state():
    """Endpoint para consultar el estado actual del visor y del motor."""
    estado = gestor_video.obtener_estado()
    estado["angulo_motor"] = controlador_motor.obtener_angulo()
    return jsonify(estado)

@app.route("/api/settings", methods=["POST"])
def update_settings():
    """Endpoint para actualizar la cámara y sobreposiciones."""
    datos = request.get_json(silent=True) or {}
    
    camara = datos.get("camara")
    sobreposicion = datos.get("sobreposicion")
    fondo_negro = datos.get("fondo_negro")
    alta_resolucion = datos.get("alta_resolucion")

    gestor_video.actualizar_configuracion(
        camara=camara,
        sobreposicion=sobreposicion,
        fondo_negro=fondo_negro,
        alta_resolucion=alta_resolucion
    )

    if "angulo_motor" in datos:
        controlador_motor.establecer_angulo(datos["angulo_motor"])

    estado = gestor_video.obtener_estado()
    estado["angulo_motor"] = controlador_motor.obtener_angulo()

    return jsonify({
        "status": "ok",
        "estado_actual": estado
    })

@app.route("/api/tilt", methods=["POST"])
def set_tilt():
    """Endpoint específico para mover el motor de la Kinect mediante ControladorMotor."""
    datos = request.get_json(silent=True) or {}
    
    if "angle" in datos:
        nuevo_angulo = controlador_motor.establecer_angulo(datos["angle"])
    elif "delta" in datos:
        nuevo_angulo = controlador_motor.modificar_angulo(float(datos["delta"]))
    elif datos.get("action") == "up":
        nuevo_angulo = controlador_motor.subir(5)
    elif datos.get("action") == "down":
        nuevo_angulo = controlador_motor.bajar(5)
    elif datos.get("action") == "center":
        nuevo_angulo = controlador_motor.centrar()
    else:
        nuevo_angulo = controlador_motor.obtener_angulo()

    estado = gestor_video.obtener_estado()
    estado["angulo_motor"] = nuevo_angulo

    return jsonify({
        "status": "ok",
        "angulo": nuevo_angulo,
        "estado_actual": estado
    })

def iniciar_servidor(host="0.0.0.0", port=5000, debug=False):
    """Lanza el servidor web."""
    print(f"\n=======================================================")
    print(f"   SERVIDOR WEB KINECT 360 ACTIVO (MÁXIMA RESOLUCIÓN)")
    print(f"   Accede desde tu navegador en: http://localhost:{port}")
    print(f"   (O http://127.0.0.1:{port})")
    print(f"=======================================================\n")
    app.run(host=host, port=port, debug=debug, threaded=True)

if __name__ == "__main__":
    iniciar_servidor()
