import cv2
import freenect

def get_rgb_frame():
    """Captura un fotograma a color (RGB) desde la Kinect 360."""
    try:
        frame, _ = freenect.sync_get_video()
        frame_bgr = cv2.cvtColor(frame, cv2.COLOR_RGB2BGR)
        
        # Aplicar efecto espejo (1 significa volteo horizontal)
        frame_espejo = cv2.flip(frame_bgr, 1)
        return frame_espejo
    except Exception as e:
        print(f"Error al obtener frame RGB: {e}")
        return None