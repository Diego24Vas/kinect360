import cv2
import numpy as np
import mediapipe as mp
from funciones.rgb_camera import get_rgb_frame

# Inicializar Hands (malla y seguimiento de manos con alta sensibilidad)
mp_hands = mp.solutions.hands
hands = mp_hands.Hands(
    static_image_mode=False,
    max_num_hands=2,
    min_detection_confidence=0.45,
    min_tracking_confidence=0.45
)
mp_drawing = mp.solutions.drawing_utils

def filtrar_manos_duplicadas(multi_hand_landmarks, multi_handedness=None, iou_umbral=0.55, dist_muñeca_umbral=0.05):
    """
    Filtra detecciones duplicadas cuando MediaPipe detecta la misma mano física dos veces.
    Usa la superposición de cajas delimitadoras (IoU) y distancia entre muñecas para nunca
    descartar dos manos reales distintas.
    """
    if not multi_hand_landmarks or len(multi_hand_landmarks) < 2:
        return multi_hand_landmarks

    scores = []
    if multi_handedness and len(multi_handedness) == len(multi_hand_landmarks):
        scores = [h.classification[0].score for h in multi_handedness]
    else:
        scores = [1.0] * len(multi_hand_landmarks)

    indices_ordenados = sorted(range(len(multi_hand_landmarks)), key=lambda i: scores[i], reverse=True)

    manos_filtradas = []
    cajas_aceptadas = []
    muñecas_aceptadas = []

    for idx in indices_ordenados:
        hand = multi_hand_landmarks[idx]
        lm = hand.landmark
        xs = [p.x for p in lm]
        ys = [p.y for p in lm]
        box = (min(xs), min(ys), max(xs), max(ys))
        wrist = (lm[0].x, lm[0].y)

        es_duplicada = False
        for a_box, a_wrist in zip(cajas_aceptadas, muñecas_aceptadas):
            xi1 = max(box[0], a_box[0])
            yi1 = max(box[1], a_box[1])
            xi2 = min(box[2], a_box[2])
            yi2 = min(box[3], a_box[3])
            inter_area = max(0.0, xi2 - xi1) * max(0.0, yi2 - yi1)
            area1 = max(0.0, box[2] - box[0]) * max(0.0, box[3] - box[1])
            area2 = max(0.0, a_box[2] - a_box[0]) * max(0.0, a_box[3] - a_box[1])
            union_area = area1 + area2 - inter_area
            iou = (inter_area / union_area) if union_area > 0 else 0.0
            dist_wrist = np.hypot(wrist[0] - a_wrist[0], wrist[1] - a_wrist[1])

            if iou > iou_umbral or dist_wrist < dist_muñeca_umbral:
                es_duplicada = True
                break

        if not es_duplicada:
            cajas_aceptadas.append(box)
            muñecas_aceptadas.append(wrist)
            manos_filtradas.append(hand)

    return manos_filtradas

def get_hand_data():
    """
    Obtiene los datos de las manos y dibuja la malla/puntos sobre un fondo negro,
    garantizando que cada mano física tenga una sola malla sin duplicados.
    """
    frame = get_rgb_frame()
    if frame is None:
        return None

    # Crear lienzo negro con las mismas dimensiones
    alto, ancho, _ = frame.shape
    lienzo_negro = np.zeros((alto, ancho, 3), dtype=np.uint8)

    # MediaPipe requiere formato RGB
    image_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
    results = hands.process(image_rgb)

    if results.multi_hand_landmarks:
        manos = filtrar_manos_duplicadas(results.multi_hand_landmarks, results.multi_handedness)
        for hand_landmarks in manos:
            mp_drawing.draw_landmarks(
                image=lienzo_negro,
                landmark_list=hand_landmarks,
                connections=mp_hands.HAND_CONNECTIONS,
                landmark_drawing_spec=mp_drawing.DrawingSpec(color=(0, 255, 0), thickness=2, circle_radius=3),
                connection_drawing_spec=mp_drawing.DrawingSpec(color=(255, 255, 255), thickness=2, circle_radius=2)
            )

    return lienzo_negro

# Alias por compatibilidad
get_hands_data = get_hand_data
