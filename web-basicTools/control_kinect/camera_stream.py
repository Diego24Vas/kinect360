"""
Administrador del flujo de video (Streaming) para la aplicación web.
Controla el estado reactivo de las cámaras, la resolución y la generación de imágenes MJPEG.
"""

import os
import sys
import time
import cv2
from threading import Lock

# Asegurar rutas de importación
DIR_ACTUAL = os.path.dirname(os.path.abspath(__file__))
DIR_WEB = os.path.abspath(os.path.join(DIR_ACTUAL, ".."))
DIRECTORIO_RAIZ = os.path.abspath(os.path.join(DIR_ACTUAL, "../.."))
DIR_PYTHON_TOOLS = os.path.join(DIRECTORIO_RAIZ, "python-basicTools")

for ruta in (DIR_ACTUAL, DIR_WEB, DIRECTORIO_RAIZ, DIR_PYTHON_TOOLS):
    if ruta not in sys.path:
        sys.path.insert(0, ruta)

try:
    from .video_processor import ProcesadorVideo
except ImportError:
    from video_processor import ProcesadorVideo

class GestorFlujoVideo:
    """Administra el estado de la cámara, los parámetros seleccionados y el streaming MJPEG."""

    def __init__(self):
        self.procesador = ProcesadorVideo()
        self._lock = Lock()
        
        # Estados actuales (Por defecto en MÁXIMA RESOLUCIÓN)
        self.tipo_camara = "rgb"           # 'rgb' | 'sensor'
        self.tipo_sobreposicion = "ninguno" # 'ninguno' | 'esqueleto' | 'rostro'
        self.fondo_negro = False
        self.alta_resolucion = True        # True = 1280x1024

    def actualizar_configuracion(self, camara=None, sobreposicion=None, fondo_negro=None, alta_resolucion=None):
        """Actualiza las opciones de visualización de forma segura entre hilos."""
        with self._lock:
            if camara in ("rgb", "sensor"):
                self.tipo_camara = camara
            if sobreposicion in ("ninguno", "esqueleto", "rostro"):
                self.tipo_sobreposicion = sobreposicion
            if isinstance(fondo_negro, bool):
                self.fondo_negro = fondo_negro
            if isinstance(alta_resolucion, bool):
                self.alta_resolucion = alta_resolucion

    def obtener_estado(self):
        """Devuelve el estado actual de las configuraciones en un diccionario."""
        with self._lock:
            res_str = "1280 × 1024 (Máxima)" if self.alta_resolucion else "640 × 480 (Estándar)"
            return {
                "camara": self.tipo_camara,
                "sobreposicion": self.tipo_sobreposicion,
                "fondo_negro": self.fondo_negro,
                "alta_resolucion": self.alta_resolucion,
                "resolucion_texto": res_str
            }

    def generar_mjpeg(self):
        """
        Generador continuo para transmisión Motion JPEG compatible con cualquier navegador web.
        """
        while True:
            t_inicio = time.time()

            # Leer parámetros actuales de manera segura
            with self._lock:
                cam = self.tipo_camara
                sob = self.tipo_sobreposicion
                fn = self.fondo_negro
                alta_res = self.alta_resolucion

            # Procesar el fotograma según las configuraciones activas
            frame = self.procesador.procesar_fotograma(
                tipo_camara=cam,
                tipo_sobreposicion=sob,
                fondo_negro=fn,
                alta_resolucion=alta_res
            )

            # Codificar a JPEG con máxima calidad visual
            exito, buffer = cv2.imencode(".jpg", frame, [cv2.IMWRITE_JPEG_QUALITY, 90])
            if not exito:
                time.sleep(0.03)
                continue

            frame_bytes = buffer.tobytes()

            # Formato estándar multipart/x-mixed-replace
            yield (
                b"--frame\r\n"
                b"Content-Type: image/jpeg\r\n"
                b"Content-Length: " + str(len(frame_bytes)).encode() + b"\r\n\r\n" +
                frame_bytes + b"\r\n"
            )

            # Control de refresco
            duracion = time.time() - t_inicio
            target_fps = 15.0 if alta_res else 30.0
            tiempo_espera = max(0.005, (1.0 / target_fps) - duracion)
            time.sleep(tiempo_espera)
