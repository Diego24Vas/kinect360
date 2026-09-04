"""
Módulo especial de funciones y controladores para Kinect 360.
Agrupa la lógica de captura, procesamiento de video, sobreposición biométrica
y administración del motor y flujos de transmisión.
"""

from .video_processor import ProcesadorVideo
from .camera_stream import GestorFlujoVideo
from .motor_controller import ControladorMotor

__all__ = ["ProcesadorVideo", "GestorFlujoVideo", "ControladorMotor"]
