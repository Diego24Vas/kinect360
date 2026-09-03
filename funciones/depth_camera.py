import cv2
import freenect
import numpy as np

def get_depth_frame():
    """Captura un fotograma de profundidad (3D) desde la Kinect 360."""
    try:
        # sync_get_depth retorna la información de profundidad en 16 bits
        frame, _ = freenect.sync_get_depth()
        
        # Normalizar los datos de 16 bits a 8 bits para poder visualizarlos con OpenCV
        depth_normalized = np.clip(frame >> 2, 0, 255).astype(np.uint8)
        
        # Aplicar un mapa de colores (colormap) para mejorar la visualización de la profundidad
        depth_colormap = cv2.applyColorMap(depth_normalized, cv2.COLORMAP_JET)
        return depth_colormap
    except Exception as e:
        print(f"Error al obtener frame de profundidad: {e}")
        return None