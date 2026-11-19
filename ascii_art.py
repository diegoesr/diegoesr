"""Convierte tu foto en arte ASCII (ascii.txt), que today.py mete en la tarjeta SVG.

Uso:  python ascii_art.py ../nuevafoto.jpeg

Parámetros que puedes ajustar abajo: ANCHO, CROP, GAMMA, NITIDEZ, RADIO, MEZCLA.
Ajustes usados con profile.jpeg (976x972): CROP=(100, 40, 730, 900), GAMMA=0.7, NITIDEZ=250, RADIO=8, MEZCLA=0.25
"""
import sys
from PIL import Image, ImageOps, ImageDraw, ImageFilter

FOTO = sys.argv[1] if len(sys.argv) > 1 else "../nuevafoto.jpeg"
ANCHO = 44                      # columnas de caracteres
CROP = (55, 10, 380, 430)       # recorte (izq, arriba, der, abajo) en px sobre la foto original
GAMMA = 1.3                     # < 1 = más relleno, > 1 = más vacío
NITIDEZ = 500                   # realce de bordes (ojos, cejas, contorno)
RADIO = 10                      # tamaño del realce: ~1 carácter en px de la foto
MEZCLA = 0.6                    # 0 = solo canal rojo (útil con ropa roja), 1 = gris normal
RAMPA = " .'`,:;!|ijl%kKH#M@"   # de vacío a denso

rgb = Image.open(FOTO).convert("RGB")
# Canal rojo mezclado con luminancia (ver MEZCLA).
img = Image.blend(rgb.split()[0], rgb.convert("L"), MEZCLA).crop(CROP)
w, h = img.size

# Máscara: cabeza (elipse) + cuello/hombros (trapecio). Lo de fuera se queda vacío.
mask = Image.new("L", (w, h), 0)
d = ImageDraw.Draw(mask)
d.ellipse((int(w * .02), 0, int(w * .98), int(h * .86)), fill=255)
d.polygon([(int(w * .28), int(h * .75)), (int(w * .85), int(h * .75)), (w, h), (int(w * .1), h)], fill=255)
mask = mask.filter(ImageFilter.GaussianBlur(15))

filas_n = int(h / w * ANCHO * 0.5)   # 0.5: un carácter es el doble de alto que de ancho
small = img.filter(ImageFilter.UnsharpMask(radius=RADIO, percent=NITIDEZ, threshold=2))
small = ImageOps.autocontrast(small.resize((ANCHO, filas_n), Image.LANCZOS), cutoff=1)
ms = mask.resize((ANCHO, filas_n), Image.LANCZOS)

n = len(RAMPA) - 1
filas = []
for y in range(filas_n):
    fila = ""
    for x in range(ANCHO):
        v = ((1 - small.getpixel((x, y)) / 255) * ms.getpixel((x, y)) / 255) ** GAMMA
        fila += RAMPA[min(n, round(v * n))]
    filas.append(fila.rstrip())

with open("ascii.txt", "w", encoding="utf-8") as f:
    f.write("\n".join(filas))
print(f"ascii.txt: {filas_n} filas x {ANCHO} columnas")
