#!/usr/bin/env python3
"""Genera las imágenes del README (assets/) con la hoja de marca del Portal Galivelop.

Hoja: https://github.com/Zeldris/Portal-Galivelop/blob/main/docs/marca.md
(papel con retícula de 24 px, filetes, chaflanes, celeste plano con isobatas, sin degradados ni movimiento;
Big Shoulders Display para títulos, Literata para frases y JetBrains Mono para datos).

GitHub muestra los SVG del README como <img>, sin acceso a fuentes externas: cada SVG lleva incrustado un
subconjunto de las tres fuentes (solo los glifos que usa, con el peso fijado).

Uso:
  python3 tools/generar_assets.py <portal> <fuentes>
    <portal>   clon de Zeldris/Portal-Galivelop (logo, isobatas, iconos y separador)
    <fuentes>  carpeta con los woff2 latinos de @fontsource-variable (big-shoulders-display, literata, jetbrains-mono)
Necesita fonttools, brotli y Pillow.
"""
import base64
import io
import re
import sys
from pathlib import Path

from fontTools import subset
from fontTools.ttLib import TTFont
from fontTools.varLib import instancer
from PIL import Image, ImageOps

RAIZ = Path(__file__).resolve().parent.parent
SALIDA = RAIZ / 'assets'

TEMAS = {
    'light': dict(papel='#fbfcfd', reticula='#eef3f6', superficie='#ffffff', filete='#b9cbd6', tinta='#13212b',
                  tinta2='#4a5c69', celeste='#1aa6df', hondo='#0072a8', enlace='#0072a8', alga='#5d7a6a'),
    'dark': dict(papel='#0d171e', reticula='#121e27', superficie='#111f29', filete='#2b3d49', tinta='#e6eef3',
                 tinta2='#9fb2bf', celeste='#1aa6df', hondo='#0b5e88', enlace='#5cc8f2', alga='#8fb09e'),
}

FUENTES = {  # familia: (archivo, peso)
    'T': ('big-shoulders-display-latin-wght-normal.woff2', 800),
    'S': ('literata-latin-wght-normal.woff2', 400),
    'M': ('jetbrains-mono-latin-wght-normal.woff2', 500),
}


def fuente(dir_fuentes: Path, clave: str, texto: str) -> str:
    archivo, peso = FUENTES[clave]
    f = TTFont(dir_fuentes / archivo)
    f = instancer.instantiateVariableFont(f, {'wght': peso})
    op = subset.Options()
    op.flavor = 'woff2'
    op.layout_features = ['kern', 'liga']
    op.name_IDs = []
    s = subset.Subsetter(op)
    s.populate(text=''.join(sorted(set(texto + texto.upper() + ' '))))
    s.subset(f)
    buf = io.BytesIO()
    f.flavor = 'woff2'
    f.save(buf)
    b64 = base64.b64encode(buf.getvalue()).decode()
    return f"@font-face{{font-family:GV{clave};src:url(data:font/woff2;base64,{b64}) format('woff2')}}"


def estilo(dir_fuentes: Path, textos: dict) -> str:
    caras = '\n'.join(fuente(dir_fuentes, k, v) for k, v in textos.items() if v)
    return (f"<style>\n{caras}\n"
            ".t{font-family:GVT,'Big Shoulders Display','Arial Narrow',sans-serif;font-weight:800}\n"
            ".s{font-family:GVS,Literata,Georgia,serif}\n"
            ".m{font-family:GVM,'JetBrains Mono',ui-monospace,monospace;font-weight:500}\n</style>")


def reticula(t, ancho, alto, x0=0, y0=0):
    lineas = [f'M{x} {y0}V{y0 + alto}' for x in range(x0 + 24, x0 + ancho, 24)]
    lineas += [f'M{x0} {y}H{x0 + ancho}' for y in range(y0 + 24, y0 + alto, 24)]
    return f'<path d="{"".join(lineas)}" stroke="{t["reticula"]}" stroke-width="1"/>'


def chaflan(x, y, w, h, c):
    """Rectángulo con la esquina superior derecha cortada a 45° (la regla 3 de la hoja)."""
    return f'M{x} {y}H{x + w - c}L{x + w} {y + c}V{y + h}H{x}Z'


LOGO = ('<path d="M0 0H100L128 28V128H0Z" fill="#1AA6DF"/><g fill="none" stroke="#fff" stroke-width="12" '
        'stroke-linecap="round" stroke-linejoin="round"><path d="M55.4 45.6 A24 24 0 1 0 64 64"/>'
        '<path d="M50 64 H80"/><path d="M71 40 L89.5 88 L108 40"/></g>')


def isobatas(portal: Path) -> str:
    svg = (portal / 'public/marca/isobatas.svg').read_text()
    # A esta escala (0,4) el filete de 1 px se perdería: se engorda para que quede en ~1,2 px.
    return ''.join(re.findall(r'<path[^>]*/>', svg)).replace('stroke-width="1"', 'stroke-width="3"')


# ---------------------------------------------------------------- banner

B_ANTE = 'FOUNDER OF GALIVELOP · SOFTWARE ARCHITECT'
B_NOMBRE = 'ÁLVARO GARCÍA GRAÑA'
B_LEMA = 'Local-first, deterministic, auditable software.'
B_DATOS = ['A CORUÑA · GALICIA', '43°22′N 8°24′W', 'GALICIA + DEVELOP']


def banner(t, portal, fuentes):
    W, H, BX = 1000, 260, 680
    css = estilo(fuentes, {'T': B_NOMBRE, 'S': B_LEMA, 'M': B_ANTE + ''.join(B_DATOS)})
    marco = chaflan(0.5, 0.5, W - 1, H - 1, 28)
    return f'''<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {W} {H}" role="img" aria-label="Álvaro García Graña, founder of Galivelop: local-first, deterministic, auditable software">
{css}
<defs><clipPath id="marco"><path d="{marco}"/></clipPath></defs>
<g clip-path="url(#marco)">
<rect width="{W}" height="{H}" fill="{t['papel']}"/>
{reticula(t, BX, H)}
<rect x="{BX}" width="{W - BX}" height="{H}" fill="{t['hondo']}"/>
<svg x="{BX}" y="0" width="{W - BX}" height="{H}" viewBox="1400 260 800 650" preserveAspectRatio="xMidYMid slice"><g fill="none" stroke="#fff" stroke-linecap="round">{isobatas(portal)}</g></svg>
</g>
<path d="{marco}" fill="none" stroke="{t['filete']}" stroke-width="1"/>
<g transform="translate(48 44) scale(0.375)">{LOGO}</g>
<text x="108" y="70" class="m" font-size="13" letter-spacing="1" fill="{t['tinta2']}">{B_ANTE}</text>
<rect x="108" y="84" width="36" height="2" fill="{t['alga']}"/>
<text x="46" y="166" class="t" font-size="66" letter-spacing="0.5" fill="{t['tinta']}">{B_NOMBRE}</text>
<text x="48" y="212" class="s" font-size="22" fill="{t['tinta2']}">{B_LEMA}</text>
<g class="m" font-size="13" letter-spacing="1" fill="#ffffff">
<text x="{BX + 32}" y="56">{B_DATOS[0]}</text>
<text x="{BX + 32}" y="78" fill-opacity="0.8">{B_DATOS[1]}</text>
<text x="{BX + 32}" y="226" fill-opacity="0.8">{B_DATOS[2]}</text>
</g>
</svg>
'''


# ---------------------------------------------------------------- diagrama

CAJAS = [  # título, frase, dato, color de categoría
    ('INPUT', 'what happens', 'action · event', 'tinta2'),
    ('DETERMINISTIC ENGINE', 'calculates the logic', 'event sourcing · book of deeds', 'hondo'),
    ('LOCAL AI', 'handles the experience', 'runs on consumer hardware', 'alga'),
]
D_PIE = 'PRIVATE · AUDITABLE · NO BLACK BOXES'


def diagrama(t, fuentes):
    W, H = 1000, 264
    xs = [(24, 192), (288, 336), (696, 280)]
    y, h = 48, 144
    css = estilo(fuentes, {'T': ''.join(c[0] for c in CAJAS), 'S': ''.join(c[1] for c in CAJAS),
                           'M': ''.join(c[2] for c in CAJAS) + D_PIE})
    partes = []
    for (x, w), (titulo, frase, dato, cat) in zip(xs, CAJAS):
        cx = x + w / 2
        partes.append(f'<path d="{chaflan(x + .5, y + .5, w, h, 14)}" fill="{t["superficie"]}" stroke="{t["filete"]}"/>')
        partes.append(f'<rect x="{x + .5}" y="{y + .5}" width="{w - 14}" height="4" fill="{t[cat]}"/>')
        partes.append(f'<text x="{cx}" y="{y + 52}" text-anchor="middle" class="t" font-size="28" letter-spacing="0.4" fill="{t["tinta"]}">{titulo}</text>')
        partes.append(f'<text x="{cx}" y="{y + 84}" text-anchor="middle" class="s" font-size="18" fill="{t["tinta2"]}">{frase}</text>')
        partes.append(f'<path d="M{x + 24} {y + 102.5}H{x + w - 24}" stroke="{t["filete"]}" stroke-dasharray="4 4"/>')
        partes.append(f'<text x="{cx}" y="{y + 126}" text-anchor="middle" class="m" font-size="13" letter-spacing="0.6" fill="{t["enlace"] if cat != "tinta2" else t["tinta2"]}">{dato.upper()}</text>')
    for (x1, w1), (x2, _) in zip(xs, xs[1:]):
        a, b, m = x1 + w1 + 12, x2 - 12, y + h / 2
        partes.append(f'<path d="M{a} {m}H{b - 4}" stroke="{t["celeste"]}" stroke-width="2.5"/>')
        partes.append(f'<path d="M{b - 12} {m - 7}L{b} {m}L{b - 12} {m + 7}Z" fill="{t["celeste"]}"/>')
    return f'''<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {W} {H}" role="img" aria-label="Input goes to a deterministic engine that calculates the logic, then to a local AI that handles the experience. Private, auditable, no black boxes.">
{css}
<rect width="{W}" height="{H}" fill="{t['papel']}"/>
{reticula(t, W, H)}
{''.join(partes)}
<rect x="{W / 2 - 18}" y="219" width="36" height="2" fill="{t['alga']}"/>
<text x="{W / 2}" y="245" text-anchor="middle" class="m" font-size="13" letter-spacing="1.2" fill="{t['tinta2']}">{D_PIE}</text>
</svg>
'''


# ---------------------------------------------------------------- iconos y separador

ICONOS = {  # nombre en assets: icono de src/assets/iconos/ del portal
    'icon-fullstack': 'papel-ventana',   # «Del prototipo al producto»
    'icon-local-ai': 'codigo',           # línea «IA local»
    'icon-deterministic': 'historial',   # event sourcing: el historial manda
    'icon-agents': 'compas',             # línea «Método» (Galivelop-workflow)
}


def iconos(portal):
    for nombre, origen in ICONOS.items():
        svg = (portal / f'src/assets/iconos/{origen}.svg').read_text()
        for tema, t in TEMAS.items():
            (SALIDA / f'{nombre}-{tema}.svg').write_text(svg.replace('currentColor', t['enlace']))


def separador(portal):
    im = Image.open(portal / 'public/marca/separador.webp').convert('RGBA')
    im.save(SALIDA / 'separator-light.webp', quality=90)
    r, g, b, a = im.split()
    inv = ImageOps.invert(Image.merge('RGB', (r, g, b)))
    Image.merge('RGBA', (*inv.split(), a)).save(SALIDA / 'separator-dark.webp', quality=90)


def main():
    portal, fuentes = Path(sys.argv[1]), Path(sys.argv[2])
    for tema, t in TEMAS.items():
        (SALIDA / f'banner-{tema}.svg').write_text(banner(t, portal, fuentes))
        (SALIDA / f'approach-{tema}.svg').write_text(diagrama(t, fuentes))
    iconos(portal)
    separador(portal)


if __name__ == '__main__':
    main()
