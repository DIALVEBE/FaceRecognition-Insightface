from pathlib import Path
from getpass import getpass
import hashlib
import hmac
import json
import secrets
import time

import cv2
from insightface.app import FaceAnalysis


# =========================
# 1. Configuracion
# =========================

UMBRAL = 0.45
ARCHIVO = Path("usuarios.json")

usuarios = json.loads(ARCHIVO.read_text()) if ARCHIVO.exists() else {}

fotos = {
    foto.stem: foto
    for foto in Path("rostros").iterdir()
    if foto.suffix.lower() in {".jpg", ".jpeg", ".png"}
}


# =========================
# 2. Identificar usuario
# =========================

usuario = input("Usuario: ").strip()

if usuario not in fotos:
    raise SystemExit("No existe fotografia del usuario")

opcion = input("Registrar (R) o Ingresar (I): ").upper()


# =========================
# 3. Registrar contraseña
# =========================

if opcion == "R":
    if usuario in usuarios:
        raise SystemExit("Usuario ya registrado")

    clave = getpass("Nueva contraseña (minimo 12 caracteres): ")

    if len(clave) < 12:
        raise SystemExit("Contraseña demasiado corta")

    if clave != getpass("Confirmar contraseña: "):
        raise SystemExit("Las contraseñas no coinciden")

    sal = secrets.token_bytes(16)

    resumen = hashlib.scrypt(clave.encode(), salt=sal, n=2**14, r=8, p=1)

    usuarios[usuario] = {"sal": sal.hex(), "hash": resumen.hex()}

    ARCHIVO.write_text(json.dumps(usuarios, indent=2))

    if __import__("os").name != "nt":
        ARCHIVO.chmod(0o600)

    raise SystemExit("Usuario registrado correctamente")


# =========================
# 4. Verificar contraseña
# =========================

if opcion != "I" or usuario not in usuarios:
    raise SystemExit("Acceso denegado")

datos = usuarios[usuario]
sal = bytes.fromhex(datos["sal"])

valida = False

for intento in range(3):
    clave = getpass("Contraseña: ")

    resumen = hashlib.scrypt(clave.encode(), salt=sal, n=2**14, r=8, p=1)

    if hmac.compare_digest(resumen.hex(), datos["hash"]):
        valida = True
        break

    print("Contraseña incorrecta")

if not valida:
    raise SystemExit("Acceso denegado")


# =========================
# 5. Preparar reconocimiento
# =========================

modelo = FaceAnalysis(name="buffalo_l", providers=["CPUExecutionProvider"])

modelo.prepare(ctx_id=-1, det_size=(320, 320))

imagen = cv2.imread(str(fotos[usuario]))

if imagen is None:
    raise SystemExit("No se pudo leer la foto")

caras = modelo.get(imagen)

if len(caras) != 1:
    raise SystemExit("La foto debe contener exactamente un rostro")

referencia = caras[0].normed_embedding


# =========================
# 6. Verificar rostro
# =========================

camara = cv2.VideoCapture(0)

if not camara.isOpened():
    raise SystemExit("No se pudo abrir la camara")

aciertos = 0
acceso = False
inicio = time.monotonic()

try:
    while time.monotonic() - inicio < 20:
        ok, imagen = camara.read()

        if not ok:
            break

        caras = modelo.get(imagen)

        if len(caras) == 1:
            vector = caras[0].normed_embedding
            similitud = float(vector @ referencia)

            if similitud >= UMBRAL:
                aciertos += 1
            else:
                aciertos = 0
        else:
            aciertos = 0

        if aciertos >= 5:
            acceso = True
            break

        cv2.putText(
            imagen,
            "Verificando identidad...",
            (20, 40),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.7,
            (0, 255, 255),
            2,
        )

        cv2.imshow("Login facial", imagen)

        if cv2.waitKey(1) & 0xFF == ord("q"):
            break

finally:
    camara.release()
    cv2.destroyAllWindows()


# =========================
# 7. Resultado
# =========================

if acceso:
    print(f"Bienvenido, {usuario}")
    print("ACCESO CONCEDIDO (demostracion)")
else:
    print("ACCESO DENEGADO")
