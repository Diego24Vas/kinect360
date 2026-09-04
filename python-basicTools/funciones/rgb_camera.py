import ctypes
import cv2
import freenect
import numpy as np

# Cargar biblioteca C de sincronización para acceder a la resolución máxima de hardware (1280x1024)
try:
    _libsync = ctypes.CDLL("libfreenect_sync.so")
except Exception:
    _libsync = None

def get_rgb_frame(alta_resolucion=True):
    """
    Captura un fotograma a color (RGB) desde la Kinect 360.
    
    Parámetros:
        alta_resolucion (bool):
            - True: Resolución MÁXIMA de hardware (1280x1024 píxeles).
            - False: Resolución estándar (640x480 píxeles).
    """
    if alta_resolucion and _libsync is not None:
        try:
            video_ptr = ctypes.c_void_p()
            ts = ctypes.c_uint32()
            # 2 = FREENECT_RESOLUTION_HIGH (1280x1024), 0 = FREENECT_VIDEO_RGB
            ret = _libsync.freenect_sync_get_video_with_res(
                ctypes.byref(video_ptr), ctypes.byref(ts), 0, 2, 0
            )
            if ret == 0 and video_ptr.value:
                buf = (ctypes.c_uint8 * (1280 * 1024 * 3)).from_address(video_ptr.value)
                frame = np.frombuffer(buf, dtype=np.uint8).reshape((1024, 1280, 3))
                frame_bgr = cv2.cvtColor(frame, cv2.COLOR_RGB2BGR)
                return cv2.flip(frame_bgr, 1)
        except Exception as e:
            print(f"Aviso: Error en resolución máxima RGB (1280x1024), usando estándar: {e}")

    try:
        frame, _ = freenect.sync_get_video()
        frame_bgr = cv2.cvtColor(frame, cv2.COLOR_RGB2BGR)
        return cv2.flip(frame_bgr, 1)
    except Exception as e:
        print(f"Error al obtener frame RGB: {e}")
        return None
