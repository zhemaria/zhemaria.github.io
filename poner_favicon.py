#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
poner_favicon.py — Inserta el bloque del favicon Ñ en los archivos HTML de un directorio.

Autor: José M. Fernández, ABE/ASE Math Master Teacher
       Harry S. Truman College — City Colleges of Chicago
Licencia: CC BY-NC-SA 4.0

USO BÁSICO
----------
  python3 poner_favicon.py .                     Simulación: informa, no escribe nada.
  python3 poner_favicon.py . --aplicar           Escribe los cambios.
  python3 poner_favicon.py ./ciencias --aplicar  Trabaja solo sobre una subcarpeta.

MODOS
-----
  --modo absoluto    (predeterminado) Enlaza a /favicon.ico, /favicon.svg, etc.
                     Para páginas alojadas en GitHub Pages.
  --modo incrustado  Inserta una sola línea con el ícono SVG dentro del propio
                     archivo. Para interactivos que se descargan o se cargan
                     en Brightspace, donde la ruta absoluta no funciona.

OPCIONES ADICIONALES
--------------------
  --respaldo         Guarda una copia .bak antes de modificar cada archivo.
  --forzar           Reemplaza los bloques de favicon que ya existan.
  --excluir CARPETA  Omite una carpeta (puede repetirse la opción).

El programa nunca modifica un archivo que ya tenga favicon, salvo con --forzar.
"""

import argparse
import os
import re
import sys

# La consola de Windows suele usar una codificación heredada (cp850) que no
# admite Ñ ni vocales acentuadas. Se fuerza UTF-8 para que el informe salga
# correcto en cualquier terminal.
for _flujo in (sys.stdout, sys.stderr):
    try:
        _flujo.reconfigure(encoding="utf-8", errors="replace")
    except (AttributeError, ValueError):
        pass

# ---------------------------------------------------------------------------
# Bloques que se insertan
# ---------------------------------------------------------------------------

BLOQUE_ABSOLUTO = """<!-- Favicon institucional Ñ -->
<link rel="icon" href="/favicon.ico" sizes="any">
<link rel="icon" type="image/svg+xml" href="/favicon.svg">
<link rel="icon" type="image/png" sizes="32x32" href="/favicon-32x32.png">
<link rel="icon" type="image/png" sizes="16x16" href="/favicon-16x16.png">
<link rel="apple-touch-icon" href="/apple-touch-icon.png">"""

_DATA_URI = (
    "data:image/svg+xml,%3Csvg%20xmlns%3D%22http%3A%2F%2Fwww.w3.org%2F2000%2Fsvg%22"
    "%20viewBox%3D%220%200%20100%20100%22%3E%3Crect%20width%3D%22100%22%20height%3D"
    "%22100%22%20fill%3D%22%23ffffff%22%2F%3E%3Crect%20x%3D%223%22%20y%3D%223%22%20"
    "width%3D%2294%22%20height%3D%2294%22%20fill%3D%22none%22%20stroke%3D%22%23002060"
    "%22%20stroke-width%3D%226%22%2F%3E%3Ctext%20x%3D%2250%22%20y%3D%2250%22%20fill%3D"
    "%22%23002060%22%20font-family%3D%22Georgia%2Cserif%22%20font-weight%3D%22700%22"
    "%20font-size%3D%2278%22%20text-anchor%3D%22middle%22%20dominant-baseline%3D%22"
    "central%22%3E%26%23209%3B%3C%2Ftext%3E%3C%2Fsvg%3E"
)

BLOQUE_INCRUSTADO = (
    '<!-- Favicon institucional Ñ (incrustado) -->\n'
    '<link rel="icon" href="' + _DATA_URI + '">'
)

# ---------------------------------------------------------------------------
# Expresiones regulares
# ---------------------------------------------------------------------------

RE_LINK = re.compile(r"<link\b[^>]*>", re.IGNORECASE)
RE_REL = re.compile(r"""\brel\s*=\s*["']([^"']*)["']""", re.IGNORECASE)
RE_CIERRA_TITLE = re.compile(r"</title\s*>", re.IGNORECASE)
RE_ABRE_HEAD = re.compile(r"<head\b[^>]*>", re.IGNORECASE)
RE_META_CHARSET = re.compile(r"<meta\b[^>]*charset[^>]*>", re.IGNORECASE)

CARPETAS_OMITIDAS = {".git", ".github", "node_modules", "__pycache__", ".vscode"}


def es_enlace_de_icono(etiqueta):
    """Determina si una etiqueta <link> declara un ícono del sitio."""
    m = RE_REL.search(etiqueta)
    if not m:
        return False
    fichas = m.group(1).lower().split()
    return any(f in ("icon", "shortcut", "apple-touch-icon", "mask-icon") for f in fichas)


def leer_texto(ruta):
    """Lee el archivo conservando el BOM y el tipo de salto de línea."""
    with open(ruta, "rb") as f:
        crudo = f.read()
    bom = crudo.startswith(b"\xef\xbb\xbf")
    if bom:
        crudo = crudo[3:]
    texto = crudo.decode("utf-8")
    salto = "\r\n" if "\r\n" in texto else "\n"
    return texto, bom, salto


def escribir_texto(ruta, texto, bom):
    datos = texto.encode("utf-8")
    if bom:
        datos = b"\xef\xbb\xbf" + datos
    with open(ruta, "wb") as f:
        f.write(datos)


def sangria_de_la_linea(texto, posicion):
    """Devuelve la sangría de la línea donde comienza la posición indicada."""
    inicio = texto.rfind("\n", 0, posicion) + 1
    linea = texto[inicio:posicion]
    return re.match(r"[ \t]*", linea).group(0)


def quitar_iconos_existentes(texto):
    """Elimina las etiquetas <link> de ícono y el comentario que las precede.

    Trabaja por líneas: si una línea contiene únicamente enlaces de ícono, se
    suprime completa, de modo que no queden líneas en blanco dentro del <head>.
    """
    salida = []
    for linea in texto.splitlines(keepends=True):
        desnuda = linea.strip()

        if re.fullmatch(r"<!--\s*Favicon institucional.*?-->", desnuda, re.IGNORECASE | re.DOTALL):
            continue

        if not RE_LINK.search(desnuda):
            salida.append(linea)
            continue

        limpia = RE_LINK.sub(
            lambda m: "" if es_enlace_de_icono(m.group(0)) else m.group(0), linea
        )
        if limpia.strip() == "":
            continue  # la línea solo tenía íconos: se suprime entera
        salida.append(limpia)

    return "".join(salida)


def procesar(ruta, bloque, forzar, respaldo, aplicar):
    """Procesa un archivo. Devuelve (estado, detalle)."""
    try:
        texto, bom, salto = leer_texto(ruta)
    except UnicodeDecodeError:
        return "error", "no se pudo leer como UTF-8"
    except OSError as e:
        return "error", str(e)

    ya_tiene = any(es_enlace_de_icono(m.group(0)) for m in RE_LINK.finditer(texto))

    if ya_tiene and not forzar:
        return "ya_tenia", ""

    original = texto
    if ya_tiene:
        texto = quitar_iconos_existentes(texto)

    # Punto de inserción: después de </title>; si no existe, después de <meta charset>;
    # si tampoco, justo después de <head>.
    m = RE_CIERRA_TITLE.search(texto) or RE_META_CHARSET.search(texto) or RE_ABRE_HEAD.search(texto)
    if not m:
        return "sin_head", "no se encontró <title>, <meta charset> ni <head>"

    sangria = sangria_de_la_linea(texto, m.start())
    bloque_sangrado = salto.join(sangria + linea for linea in bloque.split("\n"))
    texto = texto[:m.end()] + salto + bloque_sangrado + texto[m.end():]

    if texto == original:
        return "ya_tenia", ""

    if aplicar:
        try:
            if respaldo:
                escribir_texto(ruta + ".bak", original, bom)
            escribir_texto(ruta, texto, bom)
        except OSError as e:
            return "error", str(e)

    return "modificado", ""


def main():
    p = argparse.ArgumentParser(
        description="Inserta el bloque del favicon Ñ en los archivos HTML de un directorio.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    p.add_argument("carpeta", nargs="?", default=".", help="Carpeta raíz (predeterminada: la actual)")
    p.add_argument("--modo", choices=["absoluto", "incrustado"], default="absoluto",
                   help="absoluto: enlaza a /favicon.ico (GitHub Pages). "
                        "incrustado: ícono SVG dentro del archivo (Brightspace, descargas)")
    p.add_argument("--aplicar", action="store_true", help="Escribe los cambios. Sin esta opción solo simula")
    p.add_argument("--respaldo", action="store_true", help="Guarda una copia .bak de cada archivo modificado")
    p.add_argument("--forzar", action="store_true", help="Reemplaza los bloques de favicon ya existentes")
    p.add_argument("--excluir", action="append", default=[], metavar="CARPETA",
                   help="Omite una carpeta. Puede repetirse")
    args = p.parse_args()

    raiz = os.path.abspath(args.carpeta)
    if not os.path.isdir(raiz):
        print("No existe la carpeta: " + raiz)
        sys.exit(1)

    omitidas = CARPETAS_OMITIDAS | {c.strip("/\\") for c in args.excluir}
    bloque = BLOQUE_ABSOLUTO if args.modo == "absoluto" else BLOQUE_INCRUSTADO

    resultados = {"modificado": [], "ya_tenia": [], "sin_head": [], "error": []}

    for carpeta, subcarpetas, archivos in os.walk(raiz):
        subcarpetas[:] = [s for s in subcarpetas if s not in omitidas and not s.startswith(".")]
        for nombre in sorted(archivos):
            if not nombre.lower().endswith((".html", ".htm")):
                continue
            ruta = os.path.join(carpeta, nombre)
            estado, detalle = procesar(ruta, bloque, args.forzar, args.respaldo, args.aplicar)
            relativa = os.path.relpath(ruta, raiz)
            resultados[estado].append((relativa, detalle))

    # ---------------------------- Informe ----------------------------
    ancho = 74
    print()
    print("=" * ancho)
    print("  FAVICON Ñ — " + ("APLICADO" if args.aplicar else "SIMULACIÓN (no se escribió nada)"))
    print("  Carpeta: " + raiz)
    print("  Modo:    " + args.modo)
    print("=" * ancho)

    if resultados["modificado"]:
        print("\n  MODIFICADOS (%d)" % len(resultados["modificado"]))
        for ruta, _ in resultados["modificado"]:
            print("    + " + ruta)

    if resultados["ya_tenia"]:
        print("\n  YA TENÍAN FAVICON, SIN CAMBIOS (%d)" % len(resultados["ya_tenia"]))
        for ruta, _ in resultados["ya_tenia"]:
            print("    = " + ruta)

    if resultados["sin_head"]:
        print("\n  REVISAR A MANO (%d)" % len(resultados["sin_head"]))
        for ruta, detalle in resultados["sin_head"]:
            print("    ! " + ruta + "  —  " + detalle)

    if resultados["error"]:
        print("\n  ERRORES (%d)" % len(resultados["error"]))
        for ruta, detalle in resultados["error"]:
            print("    x " + ruta + "  —  " + detalle)

    total = sum(len(v) for v in resultados.values())
    print("\n" + "-" * ancho)
    print("  Archivos HTML examinados: %d" % total)
    if not args.aplicar and resultados["modificado"]:
        print("  Para escribir los cambios, repita el comando añadiendo --aplicar")
    print("-" * ancho + "\n")


if __name__ == "__main__":
    main()
