import cv2
import numpy as np
import mediapipe as mp
from mediapipe.framework.formats import landmark_pb2
from funciones.rgb_camera import get_rgb_frame 

# Inicializar Pose (esqueleto corporal)
mp_pose = mp.solutions.pose
pose = mp_pose.Pose(
    static_image_mode=False, 
    min_detection_confidence=0.5, 
    min_tracking_confidence=0.5
)
mp_drawing = mp.solutions.drawing_utils

# Conexiones exclusivas del cuerpo (sin manos/dedos: 17, 18, 19, 20, 21, 22)
CONEXIONES_CUERPO = frozenset([
    c for c in mp_pose.POSE_CONNECTIONS 
    if not any(punto in (17, 18, 19, 20, 21, 22) for punto in c)
])

def get_skeletal_data():
    """
    Obtiene los datos del cuerpo y dibuja el esqueleto corporal sobre un fondo negro,
    terminando limpiamente en las muñecas para no superponerse con la malla de manos.
    """
    frame = get_rgb_frame()
    if frame is None:
        return None
        
    # Crear un lienzo negro con las mismas dimensiones que el frame original
    alto, ancho, _ = frame.shape
    lienzo_negro = np.zeros((alto, ancho, 3), dtype=np.uint8)
    
    # MediaPipe necesita la imagen para calcular dónde están las partes del cuerpo
    image_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
    results = pose.process(image_rgb)
    
    # Dibujar el esqueleto corporal en el LIENZO NEGRO sin puntos de dedos
    if results.pose_landmarks:
        puntos_cuerpo = landmark_pb2.NormalizedLandmarkList()
        puntos_cuerpo.CopyFrom(results.pose_landmarks)
        for idx in (17, 18, 19, 20, 21, 22):
            puntos_cuerpo.landmark[idx].visibility = 0.0

        mp_drawing.draw_landmarks(
            image=lienzo_negro,
            landmark_list=puntos_cuerpo, 
            connections=CONEXIONES_CUERPO,
            landmark_drawing_spec=mp_drawing.DrawingSpec(color=(0, 165, 255), thickness=3, circle_radius=4),
            connection_drawing_spec=mp_drawing.DrawingSpec(color=(255, 0, 0), thickness=2, circle_radius=2)
        )
        
    return lienzo_negro