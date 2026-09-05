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
        """Inicializa las soluciones de MediaPipe para seguimiento esquelético, de manos y facial."""
        try:
            import mediapipe as mp
            from mediapipe.framework.formats import landmark_pb2
            self.mp = mp
            self.landmark_pb2 = landmark_pb2
            self.mp_drawing = mp.solutions.drawing_utils
            self.mp_drawing_styles = mp.solutions.drawing_styles
            
            # Modelo de pose corporal (Esqueleto)
            self.mp_pose = mp.solutions.pose
            self.pose = self.mp_pose.Pose(
                static_image_mode=False,
                min_detection_confidence=0.5,
                min_tracking_confidence=0.5
            )
            # Conexiones exclusivas del cuerpo (sin manos/dedos: 17, 18, 19, 20, 21, 22)
            self.conexiones_cuerpo = frozenset([
                c for c in self.mp_pose.POSE_CONNECTIONS 
                if not any(punto in (17, 18, 19, 20, 21, 22) for punto in c)
            ])
            
            # Modelo de manos (Malla de manos y dedos con alta sensibilidad para detectar ambas manos)
            self.mp_hands = mp.solutions.hands
            self.hands = self.mp_hands.Hands(
                static_image_mode=False,
                max_num_hands=2,
                min_detection_confidence=0.45,
                min_tracking_confidence=0.45
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

    def _filtrar_manos_duplicadas(self, multi_hand_landmarks, multi_handedness=None, iou_umbral=0.55, dist_muñeca_umbral=0.05):
        """
        Filtra detecciones duplicadas cuando MediaPipe detecta la misma mano física dos veces.
        Usa la superposición de cajas delimitadoras (IoU) y distancia de muñecas para nunca
        descartar dos manos reales distintas.
        """
        if not multi_hand_landmarks or len(multi_hand_landmarks) < 2:
            return multi_hand_landmarks

        scores = []
        if multi_handedness and len(multi_handedness) == len(multi_hand_landmarks):
            scores = [h.classification[0].score for h in multi_handedness]
        else:
            scores = [1.0] * len(multi_hand_landmarks)

        indices_ordenados = sorted(range(len(multi_hand_landmarks)), key=lambda i: scores[i], reverse=True)

        manos_filtradas = []
        cajas_aceptadas = []
        muñecas_aceptadas = []

        for idx in indices_ordenados:
            hand = multi_hand_landmarks[idx]
            lm = hand.landmark
            xs = [p.x for p in lm]
            ys = [p.y for p in lm]
            box = (min(xs), min(ys), max(xs), max(ys))
            wrist = (lm[0].x, lm[0].y)

            es_duplicada = False
            for a_box, a_wrist in zip(cajas_aceptadas, muñecas_aceptadas):
                xi1 = max(box[0], a_box[0])
                yi1 = max(box[1], a_box[1])
                xi2 = min(box[2], a_box[2])
                yi2 = min(box[3], a_box[3])
                inter_area = max(0.0, xi2 - xi1) * max(0.0, yi2 - yi1)
                area1 = max(0.0, box[2] - box[0]) * max(0.0, box[3] - box[1])
                area2 = max(0.0, a_box[2] - a_box[0]) * max(0.0, a_box[3] - a_box[1])
                union_area = area1 + area2 - inter_area
                iou = (inter_area / union_area) if union_area > 0 else 0.0
                dist_wrist = np.hypot(wrist[0] - a_wrist[0], wrist[1] - a_wrist[1])

                if iou > iou_umbral or dist_wrist < dist_muñeca_umbral:
                    es_duplicada = True
                    break

            if not es_duplicada:
                cajas_aceptadas.append(box)
                muñecas_aceptadas.append(wrist)
                manos_filtradas.append(hand)

        return manos_filtradas

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
        Detecta esqueleto corporal sobre frame_rgb y dibuja los puntos y conexiones sobre frame_destino,
        terminando en las muñecas para no interferir con la malla de manos.
        Ajusta el grosor de las líneas según la resolución.
        """
        if not self.mediapipe_disponible or frame_rgb is None:
            return frame_destino

        # Para MediaPipe es más rápido procesar en RGB
        rgb_convertido = cv2.cvtColor(frame_rgb, cv2.COLOR_BGR2RGB)
        resultados = self.pose.process(rgb_convertido)

        # Ajuste de grosor según resolución
        grosor_pose = 5 if alta_resolucion else 3
        radio_pose = 6 if alta_resolucion else 4
        grosor_conexiones = 3 if alta_resolucion else 2

        # Esqueleto corporal sin dedos/manos
        if resultados.pose_landmarks:
            puntos_cuerpo = self.landmark_pb2.NormalizedLandmarkList()
            puntos_cuerpo.CopyFrom(resultados.pose_landmarks)
            for idx in (17, 18, 19, 20, 21, 22):
                puntos_cuerpo.landmark[idx].visibility = 0.0

            self.mp_drawing.draw_landmarks(
                image=frame_destino,
                landmark_list=puntos_cuerpo,
                connections=self.conexiones_cuerpo,
                landmark_drawing_spec=self.mp_drawing.DrawingSpec(
                    color=(0, 165, 255), thickness=grosor_pose, circle_radius=radio_pose
                ),
                connection_drawing_spec=self.mp_drawing.DrawingSpec(
                    color=(255, 0, 0), thickness=grosor_conexiones, circle_radius=grosor_conexiones
                )
            )

        return frame_destino

    def dibujar_manos(self, frame_destino, frame_rgb, alta_resolucion=True):
        """
        Detecta manos sobre frame_rgb y dibuja los puntos y conexiones de los dedos sobre frame_destino.
        Filtra mallas duplicadas para que una sola mano física reciba exactamente una sola malla.
        Ajusta el grosor de las líneas según la resolución.
        """
        if not self.mediapipe_disponible or frame_rgb is None:
            return frame_destino

        rgb_convertido = cv2.cvtColor(frame_rgb, cv2.COLOR_BGR2RGB)
        resultados = self.hands.process(rgb_convertido)

        grosor = 3 if alta_resolucion else 2
        radio = 4 if alta_resolucion else 3

        if resultados.multi_hand_landmarks:
            manos = self._filtrar_manos_duplicadas(
                resultados.multi_hand_landmarks,
                resultados.multi_handedness
            )
            for hand_landmarks in manos:
                self.mp_drawing.draw_landmarks(
                    image=frame_destino,
                    landmark_list=hand_landmarks,
                    connections=self.mp_hands.HAND_CONNECTIONS,
                    landmark_drawing_spec=self.mp_drawing.DrawingSpec(
                        color=(0, 255, 0), thickness=grosor, circle_radius=radio
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
        - tipo_sobreposicion: 'ninguno', 'esqueleto', 'manos' o 'rostro'
        - fondo_negro: bool
        - alta_resolucion: bool (True = 1280x1024, False = 640x480)
        """
        frame_rgb = None
        frame_base = None

        if tipo_camara == "sensor":
            frame_base = self.capturar_frame_sensor(alta_resolucion=alta_resolucion)
            if tipo_sobreposicion in ("esqueleto", "manos", "rostro"):
                frame_rgb = self.capturar_frame_rgb(alta_resolucion=alta_resolucion)
        else:
            frame_rgb = self.capturar_frame_rgb(alta_resolucion=alta_resolucion)
            frame_base = frame_rgb

        if frame_base is None:
            return self.generar_cuadro_espera(alta_resolucion=alta_resolucion)

        if fondo_negro and tipo_sobreposicion in ("esqueleto", "manos", "rostro"):
            alto, ancho, _ = frame_base.shape
            frame_salida = np.zeros((alto, ancho, 3), dtype=np.uint8)
        else:
            frame_salida = frame_base.copy()

        if tipo_sobreposicion == "esqueleto":
            frame_deteccion = frame_rgb if frame_rgb is not None else frame_base
            frame_salida = self.dibujar_esqueleto(frame_salida, frame_deteccion, alta_resolucion=alta_resolucion)

        elif tipo_sobreposicion == "manos":
            frame_deteccion = frame_rgb if frame_rgb is not None else frame_base
            frame_salida = self.dibujar_manos(frame_salida, frame_deteccion, alta_resolucion=alta_resolucion)

        elif tipo_sobreposicion == "rostro":
            frame_deteccion = frame_rgb if frame_rgb is not None else frame_base
            frame_salida = self.dibujar_rostro(frame_salida, frame_deteccion)

        return frame_salida
