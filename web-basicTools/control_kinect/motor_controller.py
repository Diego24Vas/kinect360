"""
Controlador dedicado para el motor de inclinación (Tilt) de la Kinect 360.
Aísla exclusivamente la lógica de movimiento físico y calibración angular.
"""

import os
import sys
import ctypes
from threading import Lock

# Asegurar rutas de importación hacia python-basicTools
DIR_ACTUAL = os.path.dirname(os.path.abspath(__file__))
DIR_WEB = os.path.abspath(os.path.join(DIR_ACTUAL, ".."))
DIRECTORIO_RAIZ = os.path.abspath(os.path.join(DIR_ACTUAL, "../.."))
DIR_PYTHON_TOOLS = os.path.join(DIRECTORIO_RAIZ, "python-basicTools")

for ruta in (DIR_ACTUAL, DIR_WEB, DIRECTORIO_RAIZ, DIR_PYTHON_TOOLS):
    if ruta not in sys.path:
        sys.path.insert(0, ruta)

# Cargar biblioteca de sincronización C para control del motor
try:
    _libsync = ctypes.CDLL("libfreenect_sync.so")
except Exception:
    _libsync = None

class ControladorMotor:
    """Clase especializada para el control exclusivo del motor de inclinación de la Kinect 360."""
    
    ANGULO_MINIMO = -30
    ANGULO_MAXIMO = 30
    PASO_PREDETERMINADO = 5

    def __init__(self, indice_dispositivo=0):
        self.indice_dispositivo = indice_dispositivo
        self._angulo_actual = 0
        self._lock = Lock()

    @property
    def angulo(self):
        """Retorna el ángulo actual de inclinación."""
        with self._lock:
            return self._angulo_actual

    def obtener_angulo(self):
        """Retorna el ángulo actual de inclinación de forma segura."""
        with self._lock:
            return self._angulo_actual

    def establecer_angulo(self, angulo):
        """
        Ajusta el ángulo del motor de la Kinect a un valor específico entre -30° y +30°.
        Retorna el ángulo final alcanzado.
        """
        try:
            val = int(round(float(angulo)))
        except (ValueError, TypeError):
            val = self._angulo_actual

        angulo_clamped = max(self.ANGULO_MINIMO, min(self.ANGULO_MAXIMO, val))

        with self._lock:
            if _libsync is not None:
                try:
                    ret = _libsync.freenect_sync_set_tilt_degs(int(angulo_clamped), int(self.indice_dispositivo))
                    if ret == 0:
                        self._angulo_actual = angulo_clamped
                except Exception as e:
                    print(f"[Error ControladorMotor] Fallo al mover motor: {e}")
            else:
                self._angulo_actual = angulo_clamped

            return self._angulo_actual

    def modificar_angulo(self, delta):
        """Ajusta el ángulo actual sumando o restando un delta."""
        with self._lock:
            angulo_objetivo = self._angulo_actual + delta
        return self.establecer_angulo(angulo_objetivo)

    def subir(self, paso=None):
        """Inclina la cámara hacia arriba (+5° por defecto)."""
        p = paso if paso is not None else self.PASO_PREDETERMINADO
        return self.modificar_angulo(p)

    def bajar(self, paso=None):
        """Inclina la cámara hacia abajo (-5° por defecto)."""
        p = paso if paso is not None else self.PASO_PREDETERMINADO
        return self.modificar_angulo(-p)

    def centrar(self):
        """Restablece la cámara a su posición horizontal neutra (0°)."""
        return self.establecer_angulo(0)
