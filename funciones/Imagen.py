import cv2
import numpy as np
from freenect import sync_get_depth as get_depth
from freenect import sync_get_video as get_video
from functools import partial

screenOutDepth = partial(cv2.imshow, 'Kinect - Mapa de Profundidad')
screenOutRGB = partial(cv2.imshow, 'Kinect - Imagen RGB')

def draw():
    depth_data = get_depth()
    if depth_data is not None:
        depth = depth_data[0]
        output = depth.astype(np.uint8)
        screenOutDepth(output)

def draw_rgb():
    video_data = get_video()
    if video_data is not None:
        rgb = video_data[0]
        screenOutRGB(rgb)

def loop(delay=5):
    print("Iniciando visualización. Presiona 'q' en la ventana para salir.")
    while True:
        draw()
        draw_rgb()
        if cv2.waitKey(delay) & 0xFF == ord('q'):
            print("Cerrando aplicación...")
            break

def cerrar():
    cv2.destroyAllWindows()
