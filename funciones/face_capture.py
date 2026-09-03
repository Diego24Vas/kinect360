import cv2
import numpy as np
import mediapipe as mp
from funciones.rgb_camera import get_rgb_frame

mp_face_mesh = mp.solutions.face_mesh
face_mesh = mp_face_mesh.FaceMesh(
    static_image_mode=False,
    max_num_faces=1,
    refine_landmarks=True,
    min_detection_confidence=0.5,
    min_tracking_confidence=0.5
)
mp_drawing = mp.solutions.drawing_utils
mp_drawing_styles = mp.solutions.drawing_styles

def get_face_data():
    """
    Obtiene los datos del rostro y dibuja la malla sobre un fondo negro.
    """
    frame = get_rgb_frame()
    if frame is None:
        return None
        
    # Crear un lienzo negro con las mismas dimensiones
    alto, ancho, _ = frame.shape
    lienzo_negro = np.zeros((alto, ancho, 3), dtype=np.uint8)
    
    image_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
    results = face_mesh.process(image_rgb)
    
    if results.multi_face_landmarks:
        for face_landmarks in results.multi_face_landmarks:
            # Tesselation en el LIENZO NEGRO
            mp_drawing.draw_landmarks(
                image=lienzo_negro,
                landmark_list=face_landmarks,
                connections=mp_face_mesh.FACEMESH_TESSELATION,
                landmark_drawing_spec=None,
                connection_drawing_spec=mp_drawing_styles.get_default_face_mesh_tesselation_style()
            )
            # Contornos en el LIENZO NEGRO
            mp_drawing.draw_landmarks(
                image=lienzo_negro,
                landmark_list=face_landmarks,
                connections=mp_face_mesh.FACEMESH_CONTOURS,
                landmark_drawing_spec=None,
                connection_drawing_spec=mp_drawing_styles.get_default_face_mesh_contours_style()
            )
            
    return lienzo_negro