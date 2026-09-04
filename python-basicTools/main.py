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
    
    try:
        # 1. Ejecutar calibración de motor
        calibrador = CalibradorMotor()
        calibrador.iniciar()

        print("\nIniciando streams de video...")
        print("Presiona la tecla 'q' en las ventanas o 'Ctrl+C' en la terminal para salir.")
        
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
                
            # 3. Control de salida (con tecla 'q')
            if cv2.waitKey(1) & 0xFF == ord('q'):
                print("\nCerrando streams de video...")
                break

    except KeyboardInterrupt:
        # Esto captura el error cuando presionas Ctrl+C en la terminal
        print("\n\n[Aviso] Interrupción manual detectada (Ctrl+C). Apagando el sistema...")
        
    except Exception as e:
        # Esto captura cualquier otro error inesperado para que no rompa la terminal
        print(f"\n\n[Error] Ocurrió un problema inesperado durante la ejecución: {e}")
        
    finally:
        # 4. Limpieza garantizada (Se ejecuta SIEMPRE, haya error o no)
        cv2.destroyAllWindows()
        print("Cámaras cerradas y recursos liberados correctamente. ¡Hasta luego!")

if __name__ == "__main__":
    main()