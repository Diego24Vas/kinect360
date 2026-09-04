"""
Procesador de video para Kinect 360.
Maneja la captura de fotogramas (RGB / Profundidad) a máxima resolución (1280x1024)
"""

import os
import sys
import threading
import cv2
import numpy as np

# Asegurar acceso al directorio raíz del proyecto y a python-basicTools
DIR_ACTUAL = os.path.dirname(os.path.abspath(__file__))
DIR_WEB = os.path.abspath(os.path.join(DIR_ACTUAL, ".."))
DIRECTORIO_RAIZ = os.path.abspath(os.path.join(DIR_ACTUAL, "../.."))
DIR_PYTHON_TOOLS = os.path.join(DIRECTORIO_RAIZ, "python-basicTools")

for ruta in (DIR_ACTUAL, DIR_WEB, DIRECTORIO_RAIZ, DIR_PYTHON_TOOLS):
    if ruta not in sys.path:
        sys.path.insert(0, ruta)

try:
    from funciones.rgb_camera import get_rgb_frame
    from funciones.depth_camera import get_depth_frame
except ImportError:
    try:
        from python_basicTools.funciones.rgb_camera import get_rgb_frame
        from python_basicTools.funciones.depth_camera import get_depth_frame
    except ImportError:
        from rgb_camera import get_rgb_frame
        from depth_camera import get_depth_frame

# Candado para sincronizar llamadas a libfreenect
kinect_lock = threading.Lock()

class ProcesadorVideo:
    """Clase responsable del procesamiento, tracking y sobreposición de imágenes."""
    
    def __init__(self):
        self._inicializar_modelos()

    def _inicializar_modelos(self):
        """Inicializa las soluciones de MediaPipe para seguimiento esquelético y facial."""
        try:
            import mediapipe as mp
            self.mp = mp
            self.mp_drawing = mp.solutions.drawing_utils
            self.mp_drawing_styles = mp.solutions.drawing_styles
            
            # Modelo de cuerpo completo + manos (Holistic)
            self.mp_holistic = mp.solutions.holistic
            self.holistic = self.mp_holistic.Holistic(
                static_image_mode=False,
                min_detection_confidence=0.5,
                min_tracking_confidence=0.5
            )
            
            # Modelo de malla facial (Face Mesh)
            self.mp_face_mesh = mp.solutions.face_mesh
            self.face_mesh = self.mp_face_mesh.FaceMesh(
                static_image_mode=False,
                max_num_faces=1,
                refine_landmarks=True,
                min_detection_confidence=0.5,
                min_tracking_confidence=0.5
            )
            self.mediapipe_disponible = True
        except Exception as e:
            print(f"[Aviso] No se pudo inicializar MediaPipe: {e}")
            self.mediapipe_disponible = False

    def capturar_frame_rgb(self, alta_resolucion=True):
        """Captura un fotograma RGB con protección de hilo."""
        with kinect_lock:
            return get_rgb_frame(alta_resolucion=alta_resolucion)

    def capturar_frame_sensor(self, alta_resolucion=True):
        """Captura un fotograma del sensor de profundidad con protección de hilo."""
        with kinect_lock:
            return get_depth_frame(alta_resolucion=alta_resolucion)

    def dibujar_esqueleto(self, frame_destino, frame_rgb, alta_resolucion=True):
        """
        Detecta esqueleto y manos sobre frame_rgb y dibuja los puntos sobre frame_destino.
        Ajusta el grosor de las líneas según la resolución.
        """
        if not self.mediapipe_disponible or frame_rgb is None:
            return frame_destino

        # Para MediaPipe es más rápido procesar en RGB
        rgb_convertido = cv2.cvtColor(frame_rgb, cv2.COLOR_BGR2RGB)
        resultados = self.holistic.process(rgb_convertido)

        # Ajuste de grosor según resolución
        grosor_pose = 5 if alta_resolucion else 3
        radio_pose = 6 if alta_resolucion else 4
        grosor_conexiones = 3 if alta_resolucion else 2

        # 1. Esqueleto corporal
        if resultados.pose_landmarks:
            self.mp_drawing.draw_landmarks(
                image=frame_destino,
                landmark_list=resultados.pose_landmarks,
                connections=self.mp_holistic.POSE_CONNECTIONS,
                landmark_drawing_spec=self.mp_drawing.DrawingSpec(
                    color=(0, 165, 255), thickness=grosor_pose, circle_radius=radio_pose
                ),
                connection_drawing_spec=self.mp_drawing.DrawingSpec(
                    color=(255, 0, 0), thickness=grosor_conexiones, circle_radius=grosor_conexiones
                )
            )

        # 2. Mano izquierda
        if resultados.left_hand_landmarks:
            self.mp_drawing.draw_landmarks(
                image=frame_destino,
                landmark_list=resultados.left_hand_landmarks,
                connections=self.mp_holistic.HAND_CONNECTIONS,
                landmark_drawing_spec=self.mp_drawing.DrawingSpec(
                    color=(0, 255, 0), thickness=3 if alta_resolucion else 2, circle_radius=4 if alta_resolucion else 3
                ),
                connection_drawing_spec=self.mp_drawing.DrawingSpec(
                    color=(255, 255, 255), thickness=2, circle_radius=2
                )
            )

        # 3. Mano derecha
        if resultados.right_hand_landmarks:
            self.mp_drawing.draw_landmarks(
                image=frame_destino,
                landmark_list=resultados.right_hand_landmarks,
                connections=self.mp_holistic.HAND_CONNECTIONS,
                landmark_drawing_spec=self.mp_drawing.DrawingSpec(
                    color=(0, 255, 0), thickness=3 if alta_resolucion else 2, circle_radius=4 if alta_resolucion else 3
                ),
                connection_drawing_spec=self.mp_drawing.DrawingSpec(
                    color=(255, 255, 255), thickness=2, circle_radius=2
                )
            )

        return frame_destino

    def dibujar_rostro(self, frame_destino, frame_rgb):
        """
        Detecta malla facial sobre frame_rgb y dibuja los puntos sobre frame_destino.
        """
        if not self.mediapipe_disponible or frame_rgb is None:
            return frame_destino

        rgb_convertido = cv2.cvtColor(frame_rgb, cv2.COLOR_BGR2RGB)
        resultados = self.face_mesh.process(rgb_convertido)

        if resultados.multi_face_landmarks:
            for landmarks_rostro in resultados.multi_face_landmarks:
                # Teselación de la cara
                self.mp_drawing.draw_landmarks(
                    image=frame_destino,
                    landmark_list=landmarks_rostro,
                    connections=self.mp_face_mesh.FACEMESH_TESSELATION,
                    landmark_drawing_spec=None,
                    connection_drawing_spec=self.mp_drawing_styles.get_default_face_mesh_tesselation_style()
                )
                # Contornos del rostro
                self.mp_drawing.draw_landmarks(
                    image=frame_destino,
                    landmark_list=landmarks_rostro,
                    connections=self.mp_face_mesh.FACEMESH_CONTOURS,
                    landmark_drawing_spec=None,
                    connection_drawing_spec=self.mp_drawing_styles.get_default_face_mesh_contours_style()
                )

        return frame_destino

    def generar_cuadro_espera(self, mensaje="Esperando señal de Kinect 360...", alta_resolucion=True):
        """Genera un fotograma neutral cuando la cámara no responde."""
        alto = 1024 if alta_resolucion else 480
        ancho = 1280 if alta_resolucion else 640
        escala = 1.1 if alta_resolucion else 0.8
        pos_y = 512 if alta_resolucion else 240
        pos_x = 180 if alta_resolucion else 90

        lienzo = np.zeros((alto, ancho, 3), dtype=np.uint8)
        cv2.putText(
            lienzo,
            mensaje,
            (pos_x, pos_y),
            cv2.FONT_HERSHEY_SIMPLEX,
            escala,
            (180, 180, 180),
            2,
            cv2.LINE_AA
        )
        return lienzo

    def procesar_fotograma(self, tipo_camara="rgb", tipo_sobreposicion="ninguno", fondo_negro=False, alta_resolucion=True):
        """
        Función principal de procesamiento:
        - tipo_camara: 'rgb' o 'sensor'
        - tipo_sobreposicion: 'ninguno', 'esqueleto' o 'rostro'
        - fondo_negro: bool
        - alta_resolucion: bool (True = 1280x1024, False = 640x480)
        """
        frame_rgb = None
        frame_base = None

        if tipo_camara == "sensor":
            frame_base = self.capturar_frame_sensor(alta_resolucion=alta_resolucion)
            if tipo_sobreposicion in ("esqueleto", "rostro"):
                frame_rgb = self.capturar_frame_rgb(alta_resolucion=alta_resolucion)
        else:
            frame_rgb = self.capturar_frame_rgb(alta_resolucion=alta_resolucion)
            frame_base = frame_rgb

        if frame_base is None:
            return self.generar_cuadro_espera(alta_resolucion=alta_resolucion)

        if fondo_negro and tipo_sobreposicion in ("esqueleto", "rostro"):
            alto, ancho, _ = frame_base.shape
            frame_salida = np.zeros((alto, ancho, 3), dtype=np.uint8)
        else:
            frame_salida = frame_base.copy()

        if tipo_sobreposicion == "esqueleto":
            frame_deteccion = frame_rgb if frame_rgb is not None else frame_base
            frame_salida = self.dibujar_esqueleto(frame_salida, frame_deteccion, alta_resolucion=alta_resolucion)

        elif tipo_sobreposicion == "rostro":
            frame_deteccion = frame_rgb if frame_rgb is not None else frame_base
            frame_salida = self.dibujar_rostro(frame_salida, frame_deteccion)

        return frame_salida
