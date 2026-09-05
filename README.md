# Kinect 360 - Visor y Panel de Control en Tiempo Real

Este repositorio contiene un conjunto de herramientas y una aplicación web en Python para interactuar con la cámara y sensores de la **Microsoft Kinect para Xbox 360** (v1).

---

## 📁 Estructura del Repositorio

El proyecto se encuentra organizado en dos módulos principales:

```text
kinect360/
├── python-basicTools/             # Herramientas base de escritorio y librerías del sensor
│   ├── main.py                    # Visualizador de escritorio con OpenCV (cv2.imshow)
│   └── funciones/                 # Módulos de captura, calibración y procesamiento
│       ├── rgb_camera.py          # Captura RGB en resolución máxima (1280x1024)
│       ├── depth_camera.py        # Sensor 3D calibrado en milímetros (DEPTH_REGISTERED)
│       ├── motor_calibrator.py    # Control y calibración del motor (-30° a +30°)
│       ├── skeletal_capture.py    # Tracking de esqueleto corporal (Pose) con MediaPipe
│       ├── hand_capture.py        # Tracking de manos y dedos con MediaPipe Hands
│       └── face_capture.py        # Tracking de malla facial con MediaPipe FaceMesh
│
├── web-basicTools/                # Aplicación y servidor web reactivo
│   ├── app.py                     # Servidor Flask y endpoints REST
│   ├── control_kinect/            # Carpeta especial con funciones y controladores de la Kinect
│   │   ├── __init__.py            # Exporta GestorFlujoVideo, ProcesadorVideo y ControladorMotor
│   │   ├── camera_stream.py       # Gestor exclusivo de transmisión MJPEG y visualización
│   │   ├── motor_controller.py    # Controlador independiente para el motor de inclinación
│   │   └── video_processor.py     # Procesador de sobreposición, captura y visión artificial
│   ├── templates/
│   │   └── index.html             # Interfaz web de pantalla única (100vh)
│   └── static/
│       ├── css/style.css          # Estilos limpios, tema oscuro y diseño responsivo
│       └── js/main.js             # Lógica cliente: zoom, motor y control reactivo
│
├── requirements.txt               # Dependencias del proyecto
└── README.md                      # Documentación del repositorio
```

---

## 🛠️ Herramientas y Funcionalidades

### 1. Herramientas Base (`python-basicTools/`)
- **Cámara RGB (`rgb_camera.py`)**:
  - Captura video a color utilizando la resolución nativa máxima de hardware de la Kinect (**1280 × 1024 píxeles**, SXGA) con alternativa en resolución estándar (640 × 480).
- **Sensor de Profundidad 3D (`depth_camera.py`)**:
  - Paleta de colores predeterminada de **`freenect-glview`** (tabla gamma estándar de libfreenect), óptima para medir distancias visualmente mediante transiciones de color continuas (blanco/rojo para distancias muy cortas, pasando por amarillo, verde, cian y azul a distancias mayores, con negro para sombras y áreas fuera de rango).
  - Compatible con resolución estándar (640 × 480) y escalado de alta definición (1280 × 1024), con soporte tanto para formato nativo de 11 bits como registrado métrico.
- **Control de Motor de Inclinación (`motor_calibrator.py`)**:
  - Calibrador por teclado interactivo para terminal (CLI).
  - Función `set_motor_tilt(angulo)` compatible con transmisiones de video activas simultáneamente.
- **Biometría con MediaPipe (`skeletal_capture.py`, `hand_capture.py` y `face_capture.py`)**:
  - Detección independiente de pose corporal, malla de manos y dedos, y malla facial.
- **Visualizador de Escritorio (`main.py`)**:
  - Despliega simultáneamente las 5 ventanas de OpenCV (RGB, Profundidad, Esqueleto, Manos y Rostro).

### 2. Interfaz Web (`web-basicTools/`)
- **Pantalla Única (Single Screen)**:
  - Todo el contenido y controles se muestran ajustados al 100% de la ventana (`100vh`) sin necesidad de desplazamiento (scroll).
- **Transmisión MJPEG de Alta Calidad**:
  - Transmisión continua por HTTP (`multipart/x-mixed-replace`) a resolución máxima (1280 × 1024) y calidad JPEG al 90%.
- **Panel Lateral de Control**:
  - **Cámara**: Alterna instantáneamente entre *Cámara RGB* y *Sensor de Profundidad 3D*.
  - **Sobreponer**: Superpone en tiempo real sobre la cámara activa: *Ninguno*, *Esqueleto*, *Manos* o *Rostro*.
  - **Fondo Negro Inteligente**: Permite aislar el tracking sobre lienzo oscuro; se bloquea y deshabilita automáticamente mientras *Ninguno* esté seleccionado.
  - **Inclinación del Motor**: Ajuste con barra deslizante (`-30°` a `+30°`) y botones de acción rápida (*Bajar -5°*, *Centrar 0°*, *Subir +5°*).
  - **Zoom de Imagen Interactivo**:
    - Aumento progresivo de **1.0x a 3.5x**.
    - Botones en panel (*- Zoom*, *1.0x Restablecer*, *+ Zoom*).
    - Rueda del ratón directamente sobre el video para zoom fluido.
    - Clic y arrastre para desplazar el encuadre (Pan) con el zoom activo.
    - Doble clic para alternar rápidamente entre 2.0x y 1.0x.

---

## ⚙️ Requisitos e Instalación

### Requisitos del Sistema
- Sistema Operativo: Linux (Ubuntu / Debian).
- Dispositivo: Microsoft Xbox 360 Kinect con fuente de poder y USB conectados.
- Librerías del sistema: `libfreenect-dev`, `libfreenect-bin`.

### Entorno Conda

```bash
# 1. Activar el entorno con Python 3.10 y las librerías necesarias
conda activate kinect360

# 2. Instalar dependencias si se requiere
pip install -r requirements.txt
```

---
