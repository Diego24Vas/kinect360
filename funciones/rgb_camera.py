import cv2
import freenect
import numpy as np

def get_rgb_frame():
    """Captura un fotograma a color (RGB) desde la Kinect 360."""
    try:
        # sync_get_video retorna un array de numpy en formato RGB
        frame, _ = freenect.sync_get_video()
        # OpenCV trabaja por defecto con BGR, realizamos la conversión
        frame_bgr = cv2.cvtColor(frame, cv2.COLOR_RGB2BGR)
        return frame_bgr
    except Exception as e:
        print(f"Error al obtener frame RGB: {e}")
        return None