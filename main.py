from funciones.CalibradorMotor import CalibradorMotor
from funciones.Imagen import draw, draw_rgb, loop, cerrar

if __name__ == "__main__":
    calibrador = CalibradorMotor()
    calibrador.iniciar()

    loop()
    cerrar()
