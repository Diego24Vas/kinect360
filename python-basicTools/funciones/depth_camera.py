import cv2
import freenect
import numpy as np

def get_depth_frame(alta_resolucion=True, formato_registrado=True):
    """
    Captura un fotograma de profundidad (3D) desde la Kinect 360 con máxima calidad.
    Representación en escala de grises calibrada para corto y medio alcance:
        - Máximo brillo atenuado a gris claro (~180) para evitar sobreexposición o blancos quemados.
        - Objetos cercanos (~0.5m a 0.8m): Tonos grises medios-claros con relieve definido.
        - Objetos lejanos (> 3.0m): Tonos grises oscuros (~20).
        - Sombras / sin medición: Negro puro (0).
    
    Parámetros:
        alta_resolucion (bool):
            - True: Escala el mapa a 1280x1024 mediante interpolación bicúbica de alta definición.
            - False: Conserva la resolución nativa de 640x480.
        formato_registrado (bool):
            - True: Utiliza DEPTH_REGISTERED (calibrado en milímetros y alineado al sensor RGB).
            - False: Utiliza DEPTH_11BIT estándar.
    """
    try:
        # Intentar obtener profundidad calibrada/registrada
        if formato_registrado:
            try:
                frame, _ = freenect.sync_get_depth(0, freenect.DEPTH_REGISTERED)
            except Exception:
                frame, _ = freenect.sync_get_depth()
        else:
            frame, _ = freenect.sync_get_depth()

        if frame is None:
            return None

        # Si viene en formato calibrado/registrado (distancia en milímetros)
        if frame.max() > 2047 or formato_registrado:
            # Rango útil óptimo de Kinect v1: 400 mm (0.4 m) a 4000 mm (4.0 m)
            mask_valida = (frame >= 400) & (frame <= 4000)
            depth_norm = np.zeros_like(frame, dtype=np.uint8)
            
            # Escala de grises calibrada:
            # Se usa una curva de potencia (gamma 1.3) y techo en gris medio-claro (180/255)
            # para enriquecer los relieves en distancias cortas y evitar saturar todo en blanco.
            dist_factor = np.clip((3200.0 - frame[mask_valida]) / (3200.0 - 400.0), 0.0, 1.0)
            dist_curva = dist_factor ** 1.3
            depth_norm[mask_valida] = (20.0 + dist_curva * (180.0 - 20.0)).astype(np.uint8)

            # Filtro mediano para limpiar ruido de moteado infrarrojo preservando bordes
            depth_limpio = cv2.medianBlur(depth_norm, 3)
            
            # Formato de 3 canales (BGR en escala de grises) para compatibilidad total con stream y sobreposiciones
            depth_gray = cv2.cvtColor(depth_limpio, cv2.COLOR_GRAY2BGR)
            
            # Fondos sin medición / sombras infrarrojas en negro puro
            depth_gray[~mask_valida] = [0, 0, 0]
        else:
            # Respaldo para formato 11-bit sin registro
            mask_valida = (frame > 0) & (frame < 2047)
            depth_norm = np.zeros_like(frame, dtype=np.uint8)
            dist_factor = np.clip((950.0 - frame[mask_valida]) / (950.0 - 450.0), 0.0, 1.0)
            dist_curva = dist_factor ** 1.3
            depth_norm[mask_valida] = (20.0 + dist_curva * (180.0 - 20.0)).astype(np.uint8)
            
            depth_limpio = cv2.medianBlur(depth_norm, 3)
            depth_gray = cv2.cvtColor(depth_limpio, cv2.COLOR_GRAY2BGR)
            depth_gray[~mask_valida] = [0, 0, 0]

        # Aplicar efecto espejo para coincidir con la vista del usuario
        depth_espejo = cv2.flip(depth_gray, 1)

        # Escalar a la resolución máxima del sistema si está habilitada
        if alta_resolucion:
            depth_espejo = cv2.resize(depth_espejo, (1280, 1024), interpolation=cv2.INTER_CUBIC)

        return depth_espejo

    except Exception as e:
        print(f"Error al obtener frame de profundidad: {e}")
        return None
