"""
Servidor Web Flask para la interfaz de Kinect 360.
Expone la transmisión de video en tiempo real y endpoints de configuración.
"""

import os
import sys
from datetime import datetime
import cv2
from flask import Flask, render_template, Response, request, jsonify, send_from_directory

# Configuración de rutas para imports robustos
DIR_ACTUAL = os.path.dirname(os.path.abspath(__file__))
DIRECTORIO_RAIZ = os.path.abspath(os.path.join(DIR_ACTUAL, ".."))
DIR_PYTHON_TOOLS = os.path.join(DIRECTORIO_RAIZ, "python-basicTools")
DIR_IMG = os.path.join(DIRECTORIO_RAIZ, "img")

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

@app.route("/api/capture", methods=["POST"])
def capture_photo():
    """
    Captura una fotografía con la cámara seleccionada y sus opciones activas.
    Crea la carpeta 'img/' al momento de sacar la foto si no existe,
    y guarda el archivo con marca de tiempo.
    """
    try:
        # Crear carpeta 'img' al momento de sacar la foto si no existe
        if not os.path.exists(DIR_IMG):
            os.makedirs(DIR_IMG, exist_ok=True)

        # Obtener fotograma procesado según las opciones activas
        frame = gestor_video.obtener_fotograma_actual()
        if frame is None:
            return jsonify({
                "status": "error",
                "mensaje": "No se pudo obtener el fotograma de la cámara."
            }), 500

        # Generar nombre de archivo único con fecha y hora
        ahora = datetime.now()
        timestamp_str = ahora.strftime("%Y%m%d_%H%M%S")
        nombre_archivo = f"foto_{timestamp_str}.jpg"
        ruta_completa = os.path.join(DIR_IMG, nombre_archivo)

        # Si ya existiese una foto en el mismo segundo, añadir sufijo incremental
        contador = 1
        nombre_base, ext = os.path.splitext(nombre_archivo)
        while os.path.exists(ruta_completa):
            nombre_archivo = f"{nombre_base}_{contador}{ext}"
            ruta_completa = os.path.join(DIR_IMG, nombre_archivo)
            contador += 1

        # Guardar imagen en disco con alta calidad
        guardado = cv2.imwrite(ruta_completa, frame, [cv2.IMWRITE_JPEG_QUALITY, 95])
        if not guardado:
            return jsonify({
                "status": "error",
                "mensaje": "Error al escribir la imagen en disco."
            }), 500

        estado = gestor_video.obtener_estado()

        return jsonify({
            "status": "ok",
            "mensaje": "Fotografía guardada con éxito.",
            "archivo": nombre_archivo,
            "ruta_relativa": f"img/{nombre_archivo}",
            "url": f"/img/{nombre_archivo}",
            "fecha": ahora.strftime("%d/%m/%Y %H:%M:%S"),
            "detalles": {
                "camara": estado.get("camara"),
                "sobreposicion": estado.get("sobreposicion"),
                "fondo_negro": estado.get("fondo_negro"),
                "resolucion": estado.get("resolucion_texto")
            }
        })
    except Exception as e:
        return jsonify({
            "status": "error",
            "mensaje": f"Error al procesar la captura: {str(e)}"
        }), 500

@app.route("/img/<path:filename>")
def serve_image(filename):
    """Permite visualizar o descargar fotos almacenadas en la carpeta img/."""
    if not os.path.exists(DIR_IMG):
        os.makedirs(DIR_IMG, exist_ok=True)
    return send_from_directory(DIR_IMG, filename)

@app.route("/api/photos", methods=["GET"])
def list_photos():
    """Retorna la lista de fotografías almacenadas en la carpeta img/, ordenadas por fecha reciente."""
    if not os.path.exists(DIR_IMG):
        return jsonify({"status": "ok", "total": 0, "photos": []})

    archivos = []
    extensiones_validas = {".jpg", ".jpeg", ".png"}
    try:
        for nombre in os.listdir(DIR_IMG):
            ext = os.path.splitext(nombre)[1].lower()
            if ext in extensiones_validas:
                ruta_completa = os.path.join(DIR_IMG, nombre)
                if os.path.isfile(ruta_completa):
                    stat = os.stat(ruta_completa)
                    archivos.append({
                        "filename": nombre,
                        "url": f"/img/{nombre}",
                        "timestamp": stat.st_mtime,
                        "fecha": datetime.fromtimestamp(stat.st_mtime).strftime("%d/%m/%Y %H:%M:%S"),
                        "tamano_kb": round(stat.st_size / 1024, 1)
                    })

        archivos.sort(key=lambda x: x["timestamp"], reverse=True)
        return jsonify({
            "status": "ok",
            "total": len(archivos),
            "photos": archivos
        })
    except Exception as e:
        return jsonify({
            "status": "error",
            "mensaje": f"Error al leer la galería: {str(e)}"
        }), 500

@app.route("/api/photos/<path:filename>", methods=["DELETE"])
def delete_photo(filename):
    """Elimina una fotografía de la carpeta img/."""
    try:
        archivo_seguro = os.path.basename(filename)
        ruta_completa = os.path.join(DIR_IMG, archivo_seguro)
        if os.path.exists(ruta_completa) and os.path.isfile(ruta_completa):
            os.remove(ruta_completa)
            return jsonify({
                "status": "ok",
                "mensaje": f"Foto {archivo_seguro} eliminada exitosamente."
            })
        else:
            return jsonify({
                "status": "error",
                "mensaje": "El archivo no existe."
            }), 404
    except Exception as e:
        return jsonify({
            "status": "error",
            "mensaje": f"Error al eliminar la foto: {str(e)}"
        }), 500

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
