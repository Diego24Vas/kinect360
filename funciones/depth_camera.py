import cv2
import freenect
import numpy as np

def get_depth_frame():
    """Captura un fotograma de profundidad (3D) desde la Kinect 360."""
    try:
        frame, _ = freenect.sync_get_depth()
        depth_normalized = np.clip(frame >> 2, 0, 255).astype(np.uint8)
        depth_colormap = cv2.applyColorMap(depth_normalized, cv2.COLORMAP_JET)
        
        # Aplicar efecto espejo
        depth_espejo = cv2.flip(depth_colormap, 1)
        return depth_espejo
    except Exception as e:
        print(f"Error al obtener frame de profundidad: {e}")
        return None