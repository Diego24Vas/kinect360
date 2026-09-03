import cv2
from funciones.motor_calibrator import CalibradorMotor
from funciones.rgb_camera import get_rgb_frame
from funciones.depth_camera import get_depth_frame
from funciones.skeletal_capture import get_skeletal_data
from funciones.face_capture import get_face_data

def main():
    print("========================================")
    print("      INICIANDO SISTEMA KINECT 360      ")
    print("========================================")
    
    # 1. Ejecutar calibración de motor
    calibrador = CalibradorMotor()
    calibrador.iniciar()

    print("\nIniciando streams de video...")
    print("Presiona la tecla 'q' en cualquiera de las ventanas para salir.")
    
    # 2. Bucle principal
    while True:
        # Capturar los fotogramas de cada módulo
        rgb_image = get_rgb_frame()
        depth_image = get_depth_frame()
        skeleton_image = get_skeletal_data()
        face_image = get_face_data()
        
        # Mostrar ventanas
        if rgb_image is not None:
            cv2.imshow("1. Kinect RGB", rgb_image)
            
        if depth_image is not None:
            cv2.imshow("2. Kinect Profundidad", depth_image)
            
        if skeleton_image is not None:
            cv2.imshow("3. Kinect Esqueleto y Manos", skeleton_image)
            
        if face_image is not None:
            cv2.imshow("4. Kinect Rostro", face_image)
            
        # 3. Control de salida
        if cv2.waitKey(1) & 0xFF == ord('q'):
            print("\nCerrando streams de video...")
            break
            
    # 4. Limpieza
    cv2.destroyAllWindows()
    print("Cámaras cerradas correctamente.")

if __name__ == "__main__":
    main()