from pathlib import Path

import cv2
from insightface.app import FaceAnalysis


# =========================
# 1. Configuracion
# =========================

UMBRAL = 0.45

modelo = FaceAnalysis(name="buffalo_l", providers=["CPUExecutionProvider"])

modelo.prepare(ctx_id=-1, det_size=(320, 320))


# =========================
# 2. Registrar personas
# =========================

personas = {}

for foto in Path("rostros").iterdir():
    if foto.suffix.lower() not in {".jpg", ".jpeg", ".png"}:
        continue

    imagen = cv2.imread(str(foto))

    if imagen is None:
        continue

    caras = modelo.get(imagen)

    if len(caras) != 1:
        print(f"Omitida: {foto.name}")
        continue

    personas[foto.stem] = caras[0].normed_embedding

if not personas:
    raise SystemExit("Agrega fotografias a rostros/")

print("Personas registradas:", list(personas))


# =========================
# 3. Abrir camara
# =========================

camara = cv2.VideoCapture(0)

if not camara.isOpened():
    raise SystemExit("No se pudo abrir la camara")


# =========================
# 4. Reconocer rostros
# =========================

while True:
    ok, imagen = camara.read()

    if not ok:
        break

    caras = modelo.get(imagen)

    for cara in caras:
        if cara.normed_embedding is None:
            continue

        vector = cara.normed_embedding

        nombre, similitud = max(
            (
                (nombre, float(vector @ referencia))
                for nombre, referencia in personas.items()
            ),
            key=lambda resultado: resultado[1],
        )

        reconocido = similitud >= UMBRAL

        if reconocido:
            etiqueta = f"{nombre} ({similitud:.2f})"
            color = (0, 255, 0)
        else:
            etiqueta = "Desconocido"
            color = (0, 0, 255)

        x1, y1, x2, y2 = map(int, cara.bbox)

        cv2.rectangle(imagen, (x1, y1), (x2, y2), color, 2)

        cv2.putText(
            imagen,
            etiqueta,
            (x1, max(25, y1 - 10)),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.65,
            color,
            2,
        )

    cv2.imshow("Reconocimiento facial", imagen)

    if cv2.waitKey(1) & 0xFF == ord("q"):
        break


# =========================
# 5. Finalizar
# =========================

camara.release()
cv2.destroyAllWindows()
