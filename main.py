import cv2
from funciones.motor_calibrator import CalibradorMotor
from funciones.rgb_camera import get_rgb_frame
from funciones.depth_camera import get_depth_frame

def main():
    # 1. Ejecutar calibración de motor antes de iniciar la captura de video
    calibrador = CalibradorMotor()
    calibrador.iniciar()

    print("\nIniciando streams de video...")
    print("Presiona la tecla 'q' en cualquiera de las ventanas para salir.")
    
    while True:
        # Obtener fotogramas de ambas cámaras
        rgb_image = get_rgb_frame()
        depth_image = get_depth_frame()
        
        # Validar que las imágenes se hayan capturado correctamente
        if rgb_image is not None:
            cv2.imshow("Kinect RGB", rgb_image)
            
        if depth_image is not None:
            cv2.imshow("Kinect Depth", depth_image)
            
        # Salir del bucle al presionar 'q'
        if cv2.waitKey(1) & 0xFF == ord('q'):
            break
            
    cv2.destroyAllWindows()
    print("Cámara cerrada correctamente.")

if __name__ == "__main__":
    main()