import sys
import termios
import tty
import freenect

class CalibradorMotor:
    """Clase para calibrar el ángulo de la Kinect mediante la terminal."""
    
    def __init__(self):
        self.angulo_actual = 0

    def _obtener_tecla(self):
        """Método interno para leer teclas sin presionar Enter."""
        fd = sys.stdin.fileno()
        old_settings = termios.tcgetattr(fd)
        try:
            tty.setraw(sys.stdin.fileno())
            ch = sys.stdin.read(1)
        finally:
            termios.tcsetattr(fd, termios.TCSADRAIN, old_settings)
        return ch

    def iniciar(self):
        """Abre la cámara, inicia el bucle de teclado y cierra al terminar."""
        print("Conectando con el motor de la Kinect...")
        try:
            ctx = freenect.init()
            dev = freenect.open_device(ctx, 0)
        except Exception as e:
            print(f"Error de conexión: {e}")
            return

        # Centrar la cámara al iniciar
        freenect.set_tilt_degs(dev, float(self.angulo_actual))

        print("\n========================================")
        print("       CALIBRACIÓN DE KINECT            ")
        print("========================================")
        print("   [W] -> Subir cámara")
        print("   [S] -> Bajar cámara")
        print("   [Q] -> CONFIRMAR Y CONTINUAR")
        print("========================================\n")
        
        sys.stdout.write(f"\rÁngulo: {self.angulo_actual}°   ")
        sys.stdout.flush()

        while True:
            tecla = self._obtener_tecla().lower()

            if tecla == 'q':
                print("\n\nPosición confirmada. Liberando USB...")
                break
                
            elif tecla == 'w' and self.angulo_actual < 30:
                self.angulo_actual += 5
                freenect.set_tilt_degs(dev, float(self.angulo_actual))
                sys.stdout.write(f"\rÁngulo: {self.angulo_actual}°   ")
                sys.stdout.flush()
                
            elif tecla == 's' and self.angulo_actual > -30:
                self.angulo_actual -= 5
                freenect.set_tilt_degs(dev, float(self.angulo_actual))
                sys.stdout.write(f"\rÁngulo: {self.angulo_actual}°   ")
                sys.stdout.flush()

        # Liberamos el dispositivo para que OpenCV pueda usarlo después
        freenect.close_device(dev)