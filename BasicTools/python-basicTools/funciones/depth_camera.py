import cv2
import freenect
import numpy as np

def _crear_tabla_gamma_glview():
    """
    Genera la tabla de colores predeterminada de Kinect/libfreenect empleada en 'freenect-glview'.
    Mapea valores de profundidad de 11 bits (0 a 2047) a un gradiente continuo:
        - Muy cercano (< 0.7m): Blanco -> Rojo
        - Cercano (~0.7m a 1.1m): Rojo -> Amarillo
        - Medio (~1.1m a 1.8m): Amarillo -> Verde
        - Medio-lejano (~1.8m a 3.2m): Verde -> Cian
        - Lejano (~3.2m a 5.0m): Cian -> Azul
        - Muy lejano / Sin medición (> 5.0m o valor 2047): Negro
    """
    lut = np.zeros((2048, 3), dtype=np.uint8)
    t_gamma = np.empty(2048, dtype=np.uint16)
    for i in range(2048):
        v = i / 2048.0
        v = (v ** 3) * 6
        t_gamma[i] = int(v * 6 * 256)

    for i in range(2048):
        pval = int(t_gamma[i])
        lb = pval & 0xff
        band = pval >> 8
        if band == 0:
            r, g, b = 255, 255 - lb, 255 - lb
        elif band == 1:
            r, g, b = 255, lb, 0
        elif band == 2:
            r, g, b = 255 - lb, 255, 0
        elif band == 3:
            r, g, b = 0, 255, lb
        elif band == 4:
            r, g, b = 0, 255 - lb, 255
        elif band == 5:
            r, g, b = 0, 0, 255 - lb
        else:
            r, g, b = 0, 0, 0
        # Formato BGR para OpenCV
        lut[i] = [b, g, r]

    return lut

LUT_DEPTH_GLVIEW = _crear_tabla_gamma_glview()

def get_depth_frame(alta_resolucion=True, formato_registrado=False):
    """
    Captura un fotograma de profundidad (3D) desde la Kinect 360 con la paleta
    predeterminada de 'freenect-glview'.
    
    Parámetros:
        alta_resolucion (bool):
            - True: Escala el mapa a 1280x1024.
            - False: Conserva la resolución nativa de 640x480.
        formato_registrado (bool):
            - True: Utiliza DEPTH_REGISTERED (alineado con la cámara RGB) y proyecta
                    al rango cromático equivalente de freenect-glview.
            - False (Predeterminado): Utiliza DEPTH_11BIT nativo directo (idéntico a freenect-glview).
    """
    try:
        # Intentar obtener profundidad calibrada o 11-bit según parámetro
        if formato_registrado:
            try:
                frame, _ = freenect.sync_get_depth(0, freenect.DEPTH_REGISTERED)
            except Exception:
                frame, _ = freenect.sync_get_depth(0, freenect.DEPTH_11BIT)
        else:
            frame, _ = freenect.sync_get_depth(0, freenect.DEPTH_11BIT)

        if frame is None:
            return None

        # Si viene en formato calibrado/registrado (distancia en milímetros > 2047)
        if frame.max() > 2047 or formato_registrado:
            mask_valida = (frame >= 400) & (frame <= 4000)
            raw_indices = np.full_like(frame, 2047, dtype=np.int32)
            z_m = frame[mask_valida].astype(np.float32) / 1000.0
            raw_val = 2842.5 * (np.arctan(z_m / 0.1236) - 1.1863)
            raw_indices[mask_valida] = np.clip(raw_val, 0, 2047).astype(np.int32)
            depth_color = LUT_DEPTH_GLVIEW[raw_indices]
        else:
            # Formato nativo de 11 bits (0 a 2047) idéntico a freenect-glview
            depth_clipped = np.clip(frame, 0, 2047)
            depth_color = LUT_DEPTH_GLVIEW[depth_clipped]

        # Aplicar efecto espejo para coincidir con la vista del usuario
        depth_espejo = cv2.flip(depth_color, 1)

        # Escalar a la resolución deseada
        if alta_resolucion:
            depth_espejo = cv2.resize(depth_espejo, (1280, 1024), interpolation=cv2.INTER_LINEAR)

        return depth_espejo

    except Exception as e:
        print(f"Error al obtener frame de profundidad: {e}")
        return None
