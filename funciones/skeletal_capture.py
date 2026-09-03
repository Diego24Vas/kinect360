import cv2
import numpy as np
import mediapipe as mp
from funciones.rgb_camera import get_rgb_frame 

# Inicializar Holistic (cuerpo + manos)
mp_holistic = mp.solutions.holistic
holistic = mp_holistic.Holistic(
    static_image_mode=False, 
    min_detection_confidence=0.5, 
    min_tracking_confidence=0.5
)
mp_drawing = mp.solutions.drawing_utils

def get_skeletal_data():
    """
    Obtiene los datos del cuerpo y dibuja el esqueleto sobre un fondo negro.
    """
    frame = get_rgb_frame()
    if frame is None:
        return None
        
    # Crear un lienzo negro con las mismas dimensiones que el frame original
    alto, ancho, _ = frame.shape
    lienzo_negro = np.zeros((alto, ancho, 3), dtype=np.uint8)
    
    # MediaPipe necesita la imagen para calcular dónde están las partes del cuerpo
    image_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
    results = holistic.process(image_rgb)
    
    # 1. Dibujar el esqueleto en el LIENZO NEGRO
    if results.pose_landmarks:
        mp_drawing.draw_landmarks(
            image=lienzo_negro,  # <--- Dibujamos sobre el lienzo vacío
            landmark_list=results.pose_landmarks, 
            connections=mp_holistic.POSE_CONNECTIONS,
            landmark_drawing_spec=mp_drawing.DrawingSpec(color=(0, 165, 255), thickness=3, circle_radius=4),
            connection_drawing_spec=mp_drawing.DrawingSpec(color=(255, 0, 0), thickness=2, circle_radius=2)
        )
        
    # 2. Dibujar la mano izquierda en el LIENZO NEGRO
    if results.left_hand_landmarks:
        mp_drawing.draw_landmarks(
            image=lienzo_negro, 
            landmark_list=results.left_hand_landmarks, 
            connections=mp_holistic.HAND_CONNECTIONS,
            landmark_drawing_spec=mp_drawing.DrawingSpec(color=(0, 255, 0), thickness=2, circle_radius=3),
            connection_drawing_spec=mp_drawing.DrawingSpec(color=(255, 255, 255), thickness=2, circle_radius=2)
        )
        
    # 3. Dibujar la mano derecha en el LIENZO NEGRO
    if results.right_hand_landmarks:
        mp_drawing.draw_landmarks(
            image=lienzo_negro, 
            landmark_list=results.right_hand_landmarks, 
            connections=mp_holistic.HAND_CONNECTIONS,
            landmark_drawing_spec=mp_drawing.DrawingSpec(color=(0, 255, 0), thickness=2, circle_radius=3),
            connection_drawing_spec=mp_drawing.DrawingSpec(color=(255, 255, 255), thickness=2, circle_radius=2)
        )
        
    return lienzo_negro