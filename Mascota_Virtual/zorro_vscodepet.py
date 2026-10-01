#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
ZORRO ÁRTICO (sprite de vscode-pets)  -  Mascota de escritorio estilo "Desktop Goose"

Sprites del zorro blanco: proyecto vscode-pets de Anthony Shaw (licencia MIT)
https://github.com/tonybaloney/vscode-pets

La ventana ocupa TODA la pantalla, sin fondo (transparente) y sin bloquear tus
clics: solo el zorro (y sus huellas) reciben el ratón. Así puede moverse libre
por todo el escritorio y ves las páginas/ventanas que hay por debajo.

Qué hace (todo se activa/desactiva en Configuración, clic derecho sobre él):
  * Pasea libremente por toda la pantalla y juega (zarpazos).
  * Te PERSIGUE, te AGARRA el cursor y te lo arrastra (solo Windows).
  * Deja HUELLAS de barro por el escritorio.
  * Te trae NOTAS y MEMES empujándolos con el hocico desde fuera de la pantalla.
  * Hace "yip" (sonido, Windows).
  * Clic mantenido sobre él: lo coges y lo mueves por la pantalla.
  * DOBLE CLIC: corre a la esquina inferior derecha y se queda dormido 3 minutos.

Memes propios: imágenes .png/.gif (y .jpg con Pillow) en la carpeta "memes"
junto a este archivo o en ~/zorro_memes.

Transparencia:  Windows = color clave | macOS = alfa | Linux (X11) = extensión
SHAPE (no necesita compositor). Si tu sistema no la soporta, usa un modo
compacto (ventana pequeña que sigue al zorro). Forzarlo:  --compacto

Requisitos: Python 3.8+ con tkinter. Nada más.
"""
import base64
import collections
import json
import math
import os
import random
import sys
import threading
import time
import tkinter as tk
from tkinter import colorchooser, ttk

IS_WIN = sys.platform.startswith("win")
IS_MAC = sys.platform == "darwin"
SETTINGS_FILE = os.path.join(os.path.expanduser("~"), ".zorro_vscodepet.json")
HERE = os.path.dirname(os.path.abspath(__file__))
KEY = "#010203"                      # color que se vuelve transparente (Windows)
FW, FH = 92, 75                      # tamaño de cada fotograma del sprite
FPS_MS = 33
ANIM_DT = 0.125                      # los sprites van a 8 fps

DEFAULTS = {
    "zoom": 2, "speed": 4, "sleep_min": 3, "freq": 3,
    "wander": True, "steal": True, "prints": True, "notes": True,
    "memes": True, "sound": True,
    "mud": "#6B4E3D", "print_secs": 25,
    "note_bg": "#FFF3A8", "panel_bg": "#EAF3FA", "panel_fg": "#23364A",
    "panel_accent": "#9CC5E8",
    "messages": [
        "Hola. Soy un zorro.",
        "Me gusta tu escritorio. Ahora es mío.",
        "yip yip",
        "¿Has bebido agua hoy?",
        "Deberías descansar un poco la vista.",
        "No me toques la cola.",
        "Esta nota es muy importante (mentira).",
        "Hace mucho calor en tu pantalla...",
    ],
}
CAPTIONS = ["muy zorro, mucho nieve", "trabajar? no gracias", "yip", "sorpresa",
            "mira lo que encontré", "ñam", "hielo para todos"]

# Fotogramas PNG (base64) del zorro blanco de vscode-pets, mirando a la derecha
FRAMES = {
    "idle": [
        ("iVBORw0KGgoAAAANSUhEUgAAAFwAAABLCAYAAAD9POB7AAAB6ElEQVR4nO3bQVKDQBCFYbTcmYW5AScQbmDl5Clv"
         "EDwBN4iLuNaVC7rEnmZm3mD5fzuKCgmvpppOA10HAAAAAAAAAGjgrvUPqGUYnj9/2z9Nb03O/b7Fl/5nBC5G4GIP"
         "rX9AKbZmn8+vi/2n00vW8Typ1wRWuBiBixG42J+t4V7NPh6fqh5vHIfQ8b+xwsUIXIzAxVZr+F5nEaV45+f17VvP"
         "nxUuRuBiBC6W3If/MJuoMmso5Xp9X2xfLlPW8bb23RYrXIzAxQhcbPMsJVoTx3FY1PzWfbytyfYaZXnXMObhO0Xg"
         "YgQullxHvXmx5c2jbQ31amD0+6O/xxPtw9fOhxUuRuBiBC6W3IfbmmT70GhNtX186T49t2Zb3v+O1BrPChcjcDEC"
         "F6v2XIqdR+c+J2J59xxz/ydYXo1mlrJTBC5G4GLFZtLRWYetwdE+3hN9HtxTan7PChcjcDECF6t2X9Hro3NrdulZ"
         "iRWd16dihYsRuBiBi1WbpdiaF33v0YrWbDvL8ZTu29ewwsUIXIzAxXbznmZuDbX3HKPHy303PxUrXIzAxQhcTPaM"
         "tu3DD4fHxf7b7aOL7Lf6vl9sz/O82Pb+F0Q/vxUrXIzAxQhcrFkfbmuyV2MTamjue6NZs55UrHAxAhcjcLEvKp6k"
         "p/v4LdEAAAAASUVORK5CYII="),
        ("iVBORw0KGgoAAAANSUhEUgAAAFwAAABLCAYAAAD9POB7AAAB1klEQVR4nO3cPU7DQBDFcYPoSEFu4BNg3wDl5FFu"
         "EHMC3yAUoYYqhUeC2dldv42V/6+LLEz8tHreTD66DgAAAAAAAADQwFPrJ7CWYXj/+e/4NH02ufbnFv/0kRG4GIGL"
         "vbR+ArXYzj4eT4vjh8NH0fk8qfcEVrgYgYsRuNhmO9zr7P3+bdXzjeMQOv8NK1yMwMUIXKxah9sObDWrSOXts719"
         "e+71scLFCFyMwMWyOzxhdtG00y+Xr8Xj83kqOl/uvttihYsRuBiBiyV3eO3ZRWu2k+31WLXuUaxwMQIXI3CxzczD"
         "vXtIVHRf7u3DU2dJrHAxAhcjcLHVOtx25DgO0tlK7dcFXuenzlpY4WIELkbgYrJ9uNfpUd57jt4+PdrxXkczS7lT"
         "BC5G4GKyDrfvMVqlsxEr+nlwT63XDaxwMQIXI3Cx7F6Kzqdtp5Z29trvodp9Nx2+UQQuRuBi2ftw22n2cxq1RTvb"
         "2/dbtfftf2GFixG4GIGLVZulePvU0u/UeOy8PXq+0u/mp2KFixG4GIGLyb53Yzt8t3tdHL9ev7vIcavv+8XjeZ4X"
         "j+09xj6f6N/nYoWLEbgYgYs1+3y47WSvYxM6tPQ3qladBd2wwsUIXIzAxX4BKNafAubK0dwAAAAASUVORK5CYII="),
        ("iVBORw0KGgoAAAANSUhEUgAAAFwAAABLCAYAAAD9POB7AAAB0ElEQVR4nO3cQU7CQBSHcTTuZCE34ATCDQwnJ96A"
         "egJugAtc68pFX1JnpjP9BuL32zWNtf3n5XV4tKxWkiRJkiRJkqQOHnqfwFJ2u9fvv/YPw0eXa3/s8U//MwOHGTjs"
         "qfcJtBJ79vH4Ptp/OLxVHS8l955ghcMMHGbgsLvt4amevdm8LHq8/X5XdPxfVjjMwGEGDrvbHl4rtc5OrdvnzmKs"
         "cJiBwwwcNruHxx7Ya7485XL5HG2fTkPV8eauuyMrHGbgMAOHZffwjHnzTff0KPbkeD1Rq+u1wmEGDjNw2GQPbz1v"
         "rpU6n1Kl6/LUOjz3c4kVDjNwmIHDFpuH9362r/U9JtXzc2ctVjjMwGEGDpvso6Xr3tKe2Wq+PIU+X2cpN8rAYQYO"
         "w55Lid8xRrWzkaj0efCUVp8brHCYgcMMHJbdl2rn0bGn1vbspefxcd1tD79TBg4zcFj2Ojz2sPhcxtJKe3Zq3R+1"
         "XrdPscJhBg4zcNjsWUrpurT2nZqU+J1j6fFq383PZYXDDBxm4DDsGe7Yw9fr59H+6/VrVbI/2m63o+3z+Tzajvec"
         "eD6lfz+XFQ4zcJiBw7q9ax97cqrHZvTQ2t+oQmZDVjjMwGEGDvsBDvacVuu7Q9UAAAAASUVORK5CYII="),
        ("iVBORw0KGgoAAAANSUhEUgAAAFwAAABLCAYAAAD9POB7AAAB00lEQVR4nO3cwW2DQBCFYRxxiw9xB1QQ6CBy5VY6"
         "MKmADpyDc05OjsQoeHfY5S04/3dDKBt4Wo3HY+yqAgAAAAAAAAAUsCt9AUtp29fve+f7/qPIvT+V+Kf/GYGLEbhY"
         "XfoCcrE1+3R6H50/Ht+S1guJfU1gh4sRuBiBi222hodq9uHwsuh6Xde61r9hh4sRuBiBi222hqcK9dmhvn3uLIYd"
         "LkbgYgQu9rA1/HL5HB2fz33SenP7bosdLkbgYgQu9rA1PMTWZDs7sf6Yr4/6eObhK0XgYgQulu3ZjKU+A5xaP1Rz"
         "Le983PL24VP3xw4XI3AxAheL7sNDNdo7q+i6dlYfGyu1Zluh+4ut8exwMQIXI3Cx37rprdF23uytmbnmy1NCfXru"
         "62WWslIELkbgYvWtdqc+m2drupd3NhLifR48JNf7BHa4GIGLEbjYzjvHziW1ZueelVi276aGbxSBixG4WK36znnq"
         "a8XS7wty9+1T2OFiBC5G4GKrebYwtYbaeb13vdTv5sdih4sRuBiBi8l+98n24fv98+j89fpVec5bTdOMjodhGB3b"
         "9xv2erx/Pxc7XIzAxQhcrFgfbmtyqMZG1NDU59Mlnwuww8UIXIzAxX4Ar5SQVL3p/8cAAAAASUVORK5CYII="),
        ("iVBORw0KGgoAAAANSUhEUgAAAFwAAABLCAYAAAD9POB7AAAB3ElEQVR4nO3bQU6DQBjFcTTu7MLegBMINzA9eeMN"
         "iifgBnVR17rqgi/Sb76Z4UH1/9sRAoWXyWMyhaYBAAAAAAAAAKzgYe0LWErXvX7f2j8MH6vc++MaP/qfEbgYgYs9"
         "rX0BtdjOPh7fJ/sPh7ei83lSnwmMcDECFyNwsbvtcK+z9/uXRc/X913o/FeMcDECFyNwsbvt8FLePNubt+euxTDC"
         "xQhcjMDF/myHn8+fk+3TaSg6X+6822KEixG4GIGLVevwpdaPl2I72a6dWL+sr0/ul/XwjSJwMQIXy+5R29nRea7t"
         "UK8DvfVqT3R93IrOw+fuhxEuRuBiBC6WPA8v7WzLHt/3Xda8dk5pZ1ve/aZ2PCNcjMDFCFxstidL572W16m11puv"
         "vOuNdrx3faylbBSBixG4WLX1cO89Du997dJnRPR6omqt3zPCxQhcjMDFsjvcdqTXcfY/wKXn9Vt5D8VihIsRuBiB"
         "iyV3eLSza4uufdh3Cz215+1zGOFiBC5G4GKzHa7u6NIOtfPu6PlKv81PxQgXI3AxAheT9bT9j3S3e57sv1y+msh+"
         "q23byfY4jpNt+0yy1xM9PhcjXIzAxQhcbLXvNG0nex2b0KGl3xiFjs/FCBcjcDECF/sBR4uY0cGLxIgAAAAASUVO"
         "RK5CYII="),
    ],
    "walk": [
        ("iVBORw0KGgoAAAANSUhEUgAAAFwAAABLCAYAAAD9POB7AAAB6ElEQVR4nO3cQVKDQBCFYbTcmYW5AScI3MDKyVPe"
         "IHgCbhAXca0rF9Nl7GlmeEPK/9tRlAReTTVNh9h1AAAAAAAAAIAGHlqfwFqG4fD11/5pem9y7Y8tPvQ/I3AxAhd7"
         "an0CtdiafTq9JfuPx9ei43ly7wmscDECFyNwsbut4V7N3u9fVj3eOA6h4/9ghYsRuBiBi2XX8K3OJpbyrsfr25de"
         "LytcjMDFCFxscR/+y6xiUzX+cvlIts/nqeh4S/tuixUuRuBiBC5WbZbi1chxHJIa37pvtzXZ3pMs757FPHyjCFyM"
         "wMWy66g3L7a8ebStoV4NjH5+9Hw80T781vWwwsUIXIzAxbL7cFuTbB8aram2b6/dp5fWbCvjOSPrOKxwMQIXI3Cx"
         "1d5LsfPo0vdELO87x9LnBMur0cxSNorAxQhcrNpMOjrrsDU42sd7ou+De2rN71nhYgQuRuBiq32v6PXRpTW79qzE"
         "is7rc7HCxQhcjMDFVpul2JoX/d2jFa3Zdpbjqd2338IKFyNwMQIX28zvNEtrqP3OMXq80t/m52KFixG4GIGLyd7R"
         "tn34bvec7L9eP7vIfqvv+2R7nudk23suiP79UqxwMQIXI3CxZn24rclejc2ooaX/o6po1pOLFS5G4GIELvYNg4+k"
         "p4+XXK4AAAAASUVORK5CYII="),
        ("iVBORw0KGgoAAAANSUhEUgAAAFwAAABLCAYAAAD9POB7AAABy0lEQVR4nO3bzW3CQBCGYRLlFg6hA1cQ0wFyx6QC"
         "lA5wKqADciDn5JSDR8azv98a6X1uFrAxn1aTYWxvNgAAAAAAAACABp5an0Apff/+G/P+cfxa/O6l1/v3HLMo8hG4"
         "GIGLvbQ+gVS2xp5On4vv3+3eJsf7fb9Yo+16M5/3TnEWO1yMwMUIXKxYDbc1NbQvrSW35g7DYfH11O/HDhcjcDEC"
         "F0uu4V4fPAyHpjX9ev2eHJ/PY9Z6qX23xQ4XI3AxAhcLruFezbZ979rZmuzNYkr9j2KHixG4GIGLPcw8PHb+7Ynt"
         "y70+PHSWxA4XI3AxAherVsNtjbTXEGvPVkr/LvBqfuishR0uRuBiBC4m68O9mh7Lu+YYe5+Kx6vRzFJWisDFCFxM"
         "VsPtNUYrdzZieTU+VqnfDexwMQIXI3Cx5LoUO5+2NTW3Zte+hlqq77bY4WIELkbgYsl9uK1h9j6N0ry+2s5qvL7f"
         "W3/mPpSo9e5hh4sRuBiBizV7Difg/vLJcdd1k+Pj8WNx/dz7ue3fu1wuk2P68AdB4GIELraaGr7dvk5ev91+stbP"
         "nV/Xeu6UHS5G4GIELraaGm61fla/Fna4GIGLETgAAIH+ABK9juhK7oWaAAAAAElFTkSuQmCC"),
        ("iVBORw0KGgoAAAANSUhEUgAAAFwAAABLCAYAAAD9POB7AAAByElEQVR4nO3bzU3DQBCG4YAogHTgCnA6iHxFSq+h"
         "gogOYipwB6EDOHHYkb3j/fFnG73PbZWwOJ9Wk/VkfTgAAAAAAIAde1r7Ampp27eflPf3/Vf0s9ee789zyqQoR+Bi"
         "BC72svYF5LI19nb7jL7/eHwNxqdTG63Rdr6Rv/cucRQrXIzAxQhcbLc13FNac7vuHH197r7bYoWLEbgYgYtl13C7"
         "D86taUt5PL6D8f3eF82Xu++2WOFiBC5G4GKza7jXu+i686ZrumVrsteLqfV5WeFiBC5G4GKTNdyr2bZXsbTU/rcn"
         "dV/u7cPn3pewwsUIXIzAxRbrh3vnOpbep9f+jvFq/txeCytcjMDFCFxsso6Wnvvw1OovT1FfL72UjSJwMQIXk51L"
         "sb8xWqW9Ecs7V5Kq1n0DK1yMwMUIXGx2XSrtR9uaWlqzl+7H2303NXynCFyMwMWy61Lqc4xW6XeAZfvV3r7fm3/k"
         "HEow5nz4ThC4GIGLrXb+b8ZZxWDcNE0wvl4/ovOX9tvt/xuGIRhTw3eCwMUIXGwzz2leLu/R120NrfUbY0TRfcYU"
         "VrgYgYsRuNhm9uHW1p8RysUKFyNwMQIHAAAA8O/9AlEYis3pBTDzAAAAAElFTkSuQmCC"),
        ("iVBORw0KGgoAAAANSUhEUgAAAFwAAABLCAYAAAD9POB7AAAB2ElEQVR4nO3cwU3DQBCF4YC4kQPpwBVgd4DScagg"
         "ooOYCtJBOIQznEDaEfbseuxnO/zfzbK0iZ9Wk8nEzmYDAAAAAABW7G7uNzCVun7+6jvftu+zXPv9HC/6nxG4GIGL"
         "Pcz9BsZia/bx+Jac3+9fQut5cj8T2OFiBC5G4GKrreFezd7tniZdr2nqovV/sMPFCFyMwMVWW8OjvD7b69uHzmLY"
         "4WIELkbgYjdbwy+Xj+T4dGpD6w3tuy12uBiBixG42M3WcI+tyXZ2Yv0xX0/6eObhC0XgYgQu1ll37KzBq1FT/QbY"
         "tb5Xc63S+bhV2od3XR87XIzAxQhc7LcPz7ivo7dGl84qmqYe1MfmitZsy7u+3BrPDhcjcDECF8uepdgaZufNUaV9"
         "vPebo9enl9Z4r0YzS1koAhcjcLHOGl5a46I1vXQ24im9H9wz1vcEdrgYgYsRuFj2PHxs0Zo99qzEGqvvttjhYgQu"
         "RuBinX342PPp6GeC11dHZz12/ehznl3Y4WIELkbgYrP9X0rps/FVVSXHh8Nr7/rR+7nt653P5+SYPnwlCFyMwMUW"
         "U8O328fk/PX6GVo/+j2i9N7KXOxwMQIXI3CxxdRwa67/FZwaO1yMwMUIHACATN9CL43OALU0AgAAAABJRU5ErkJg"
         "gg=="),
        ("iVBORw0KGgoAAAANSUhEUgAAAFwAAABLCAYAAAD9POB7AAABtUlEQVR4nO3cQW7CMBCFYVp1VxblBjkB4QYV20qc"
         "GfUGhBPkBnRB1+0qSLYIk4md56T9v10UNTVPo4k1WKxWAAAAAAAAAAAAAByeSi9gKnW9/Xl0v2nORT77c4l/+p8R"
         "uBiBi72UXkAucc8+Hj+D+/v9e9LzLEPfCVS4GIGLEbjYYnu41bM3m7dJn7fb1a7nd6hwMQIXI3CxxfbwVNY+29q3"
         "j53FUOFiBC5G4GJ/todfLl/B9enUJD1v7L47RoWLEbgYgYvderh3/puq1HeKnbgnx7OT2J35epAX8/CZInAxAhe7"
         "9Z3c82VL3EOtHmitz5K6fu8+vO/zUOFiBC5G4GK9fXNuPd3bw3OvzzL0nUSFixG4GIGLDZ5nTL0PzjVv7uTu8db6"
         "mKXMFIGLEbjY6Jm0d35undf2vhMs3vPgllzzeypcjMDFCFxM9r1i6j4+NvWsxDuvH4oKFyNwMQIXW8zZQm/Pjs8W"
         "WnLv2/tQ4WIELkbgYsV6+OHwEVxfr9/B9Xr9+vB+rKqq4LptW9d6Uv9+KCpcjMDFCFysWA+Pe7J1DiV2Z7aR+htX"
         "kvPxVLgYgYsRuNgvAPGCpbCxW00AAAAASUVORK5CYII="),
        ("iVBORw0KGgoAAAANSUhEUgAAAFwAAABLCAYAAAD9POB7AAABzklEQVR4nO3aQU6DQBjF8Wrc2YW9ASewvUHDmZt0"
         "23iD4gm4QV3Uta5MnC/Ax8cMDzT/347QIn2ZPMZhNhsAAAAAAAAAwAIelr6BUvb716/I55vmffC3l77ej8fIRZGP"
         "wMUIXOxp6RuYynbs5fI2+Pnd7iU5Phz2gx1tr9fxfe8WOzHCxQhcjMDF/myHe3I7t66Pg+fHzrstRrgYgYsRuNi/"
         "7fDb7SM5vl6brOtNnXdbjHAxAhcjcLHJHT7XerGK7WRvLcaer+tj8vtZD18pAhcjcLHRvWo7OzqvtZ0Z7fTo+rdl"
         "11aiovPwvt/HCBcjcDECF+udh3udadcqLNuZtvPtO8XS8/Tczra8Z9bYjmeEixG4GIGLTV5Lse/8ovNir9Ojf9+K"
         "7lPxeB3NWspKEbgYgYv19o633m07K7rWkfsM8HgdH1Xq/wRGuBiBixG42GzvGb1nQG5nR/cOqtfv+zDCxQhcjMDF"
         "inW47ezt9jk5fzqds65f+p1kxz6T5HiufTSMcDECFyNwsdk6fGlVVSXHbdsOfl6195ERLkbgYgQutqo927958/r7"
         "/TM59tbnraX2qzPCxQhcjMDFVtvh1lo7OYoRLkbgYgQOAMBI333Wi6swHmb6AAAAAElFTkSuQmCC"),
        ("iVBORw0KGgoAAAANSUhEUgAAAFwAAABLCAYAAAD9POB7AAABzklEQVR4nO3cQU6DUBDG8Wrc2YW9ASeQ3qDhzE3c"
         "Nt6geAJuUBd1rSsXTJBh3nt8gPn/doSK8GUyfRme7nYAAAAAAGDDHpa+gVLq+vU78vm2/Rh99tLX+/UYuSjyEbgY"
         "gYs9LX0DqWyPvVzeRz9/OLz0jo/HerRH2+sN/Lx3i4OocDECFyNwsc32cE9uz22a0+j5qetuiwoXI3AxAheb3MOj"
         "swUrteelut0+e8fXa5t1vdR1t0WFixG4GIGLJa/Dc2cX6p5u2Z7sPY893zSnpOehwsUIXIzAxZL7qDePtj3csj00"
         "+o7R67mWdz+e6Dr8r+ehwsUIXIzAxRabh9vZRul1em7PtrxZzNQeT4WLEbgYgYsVm2fYdbLX8+y82nuHGBWd9Xi8"
         "Hs0sZaUIXIzAxWZbh9sebdmeHZ2NeEp/J5Sa31PhYgQuRuBis71X9Pax5Pbs6N7B6L6U6Lx+KipcjMDFCFxstlnK"
         "fv/cO38+v2Vdv/Q7yYF9Jr3jufbNUOFiBC5G4GKz9fC1qaqqd9x1Xe9YtdeRChcjcDECFys2Dy/dA711/f3+Ff39"
         "q/iOocLFCFyMwMU28z+vvHX+0n8zNBUVLkbgYgQOAAAA4N/7ATjuhZtBiCBMAAAAAElFTkSuQmCC"),
        ("iVBORw0KGgoAAAANSUhEUgAAAFwAAABLCAYAAAD9POB7AAAB1ElEQVR4nO3cMU7DQBCF4YDoSEFu4BPg3CDymSOl"
         "jbhBzAlyg1CEGiqKHTmeHe/62Uj/11kxxn4aDct4lc0GAAAAAAAAALCAp6VvoJa2ff+JnN/3n6PPXvt6f54jF0U5"
         "AhcjcLGXpW9gKttjz+eP0fN3u7fkeL9vR3u0vd7Az3u3OIgKFyNwMQIX+7c93FPac7vuMPp57rrbosLFCFyMwMUe"
         "9vDoLMEztedNdbt9JceXS190vanrbosKFyNwMQIXy16HR2cVlp1dqHu6ZXuy93z28647THoeKlyMwMUIXCy7j5bO"
         "ny3bQ6PvGL3fH70fT3Qd/uh5qHAxAhcjcLHsdbjtSXYdGu2pdrZRe51e2rMtbxaT2+OpcDECFyNwsdneadp5dLSn"
         "evN4751j6f8JltejmaWsFIGLEbhYtZl0dNZhe3B0He/xenxUrfk9FS5G4GIELjbbe0VvHV3as6N7B6P7UqLz+lxU"
         "uBiBixG42Gzr8O32Nfn8eDwVXb/2O8mBfSbJ8Vz7ZqhwMQIXI3Cx2Xr40pqmSY6v1+vo+aq9jlS4GIGLEbjYar8v"
         "xVvX3+/fybHtwd7flKX2p1PhYgQuRuBiq+3h1lp7chQVLkbgYgQOAECmX34di1VxtTc0AAAAAElFTkSuQmCC"),
    ],
    "run": [
        ("iVBORw0KGgoAAAANSUhEUgAAAFwAAABLCAYAAAD9POB7AAABjUlEQVR4nO3bQU7CQBjF8WrYyUJu0BPQ3sBwcuIN"
         "qCfoDXCBa12ROC/CNzNtX0n8/3akUsaXycvkozQNAAAAAAAAAAAAAAAAAAAAACziqfaNXbf//v16GD6q77UEXZ9a"
         "a73Pa3zof0bgZgRutsn9Q+3E02lIrvd9t2qn6/qOx/fk+uHwNul+kdz/lx1uRuBmBG52s8Ojzl5b1Nm73eui9+v7"
         "ruj+V+xwMwI3I3Cz7HP4+fyZvI468lFnGVfR+qJze+362eFmBG5G4GbZHa6000vP6Tp7mdvU9anac7dih5sRuBmB"
         "m1V3eCntVKWzi0jpfFtpJ0ef/8d8vWr+zw43I3AzAjfLngdE8+KIdq77/aXzcVV6Dr/V6exwMwI3I3Cz7HO4dpKe"
         "Q92mdnKpaBaT2/HscDMCNyNwM9v3inM/+xeZ+zmaqKOZpTwoAjcjcLPVOny7fUmuXy5fTcl11bZt8nocx8IV3jfX"
         "czTscDMCNyNwM9t3mko7WTuy4negk55lLP1NTy12uBmBmxG42Q/KN4aUL/qGSgAAAABJRU5ErkJggg=="),
        ("iVBORw0KGgoAAAANSUhEUgAAAFwAAABLCAYAAAD9POB7AAABwElEQVR4nO3cUU7CQBSFYTC+yYNsxLIDwwpkB4aV"
         "EndAXUF3gDvQp5LMjXp7O9PTDvzfW0Mo9WRymFxaVysAAAAAAFCx9dwXMJWmefn+7/W2/Zzlb3+Y40PvGYGLEbjY"
         "49wXUIrt7NPpI3l9v3/NOp9n6HcCK1yMwMUIXKzaDvc6e7t9nvR8u10TOn+PFS5G4GIELlZth+fy9tnevn3sLIYV"
         "LkbgYgQudrMdfrl8Jcfnc5t1vrH7bosVLkbgYgQudrMd7rGdbGcn1i/z9WQfzzx8oQhcjMDFqrkvxZtXe6LzcSu6"
         "D/+r01nhYgQuRuBi1e7Dczs5ypvFDO14VrgYgYsRuFi1+3BP7vzb8jqaWcpCEbgYgYsV24eXvp86d3ZS6jfIXqln"
         "gljhYgQuRuBig3vJ6+jovtfrWK+zo7OU6OdFnwliH75QBC5G4GLXfXi0o+29e7lKd7Zlr/9weEuObWfb6zke35Pj"
         "rutGXQcrXIzAxQhcbN13d3QfHe1wryM9XoeXnp14eManEgQuRuBi13341B242TxlvT939mK/Q/ifV3eCwMUIXEzW"
         "Y9HfPK3ob6DR96uwwsUIXIzAAQAY6AcYQ4F6A/Gc7AAAAABJRU5ErkJggg=="),
        ("iVBORw0KGgoAAAANSUhEUgAAAFwAAABLCAYAAAD9POB7AAABf0lEQVR4nO3azW3CQBCGYYi4hUNoJKYDRAXQQUSl"
         "KB3gVOAOoIPkBNKOEsbDmM8/eZ+bBazXn1bj1bCzGQB0Zt73BJ6lqt6/731e11+9PPtLHzf9zwhcjMDFFn1PoCu2"
         "Zh+Pn8Xn2+0mNZ6n7TuBFS5G4GIELjbaGu7V7NXq7anjrddVaPwrVrgYgYsRuNhoa3iWt8/29u2P9mJY4WIELkbg"
         "YpOt4efzpbg+nerUeI/uuy1WuBiBixG42GRruMfWZNs7sX7prxf7ePrhA0XgYgQuNppzKV6/2hPtj1vRffhfNZ0V"
         "LkbgYgQu1tk+PHqOIytbk6O8XkzbGs8KFyNwMQIXa13DvRod7TdHexne77Pzyd6PXspAEbgYgYvdani0Rtv/DD3Z"
         "mu3Nx7vfULDCxQhcjMDFFtfand232ppuz+Ytl6+p8aO9E+959vtdcd00TXFt3zGHw8fd77fFChcjcDECF5ur+9hT"
         "wfnwkSBwMQIHAAAAAAAAAAAAAAAAJuAHeq5mVuqzUXkAAAAASUVORK5CYII="),
        ("iVBORw0KGgoAAAANSUhEUgAAAFwAAABLCAYAAAD9POB7AAABoUlEQVR4nO3bzW3CQBCGYRLlFg6hA1eA3QFyJRGV"
         "onSAU4E7IB0kJ5B2JDLMrv2tgfe5WQT/fFqNV8NktQIAAAAAAAAAAAAQ8FL7BubSttvf/z4fhu8qz/5a46LPjMDF"
         "CFzsrfYNTMXW7MPhK/m873dF5/Pc+k5ghYsRuBiBi91tDfdq9mbzMev5uq4Nnf+MFS5G4GIELna1hkf3oVG1ehln"
         "3vN5+/bc+2eFixG4GIGLXWq4rWnH4zDrhbuuTa43dU0/nX6S49Lnyd13W6xwMQIXI3CxS92M7rttTbQ1M9rLKK2R"
         "tvdheb0Q7/uW3afTD18oAhcjcLHsva9X872aaGvg1H9vRd8pVvQdc62ms8LFCFyMwMWyf9P09p19vyuq8Z7Smhzl"
         "9WJurfGscDECFyNwMdlcynr9XvR9W0NLey/R/rh3PXopC0XgYgQuJpsNKZ1zKf1N0vbro/PiFnMpd4LAxQhcTLYP"
         "L507sXMsUfYd0DRNcjyOY3Jsez37/ac9ZdZcDStcjMDFCFzsYf/X3lrKvDsrXIzAxQgcAAAAwMP7A06NeZCSxTvb"
         "AAAAAElFTkSuQmCC"),
        ("iVBORw0KGgoAAAANSUhEUgAAAFwAAABLCAYAAAD9POB7AAABkUlEQVR4nO3aTW6CUBTFcdp0poO6kcIOGlfSuFLT"
         "HUhXwA50YMftqEk5Mbm8Dw4Y/78ZefjEk5fr40LTAAAAAAAAAAAAAAAAAACwak+1Jmrbt5//x33/VW3uHHo9aqnr"
         "e17iSx8ZgZsRuNlL7ge1Rp5O/Wi861prTdfrOR4/R+P7/XvRfJGpv48VbkbgZgRuNrmGRzXbLarZu93rrPN1XZs0"
         "/x9WuBmBmxG4WfY+/Hy+jI5Ta+bSon12tG/Pva9ghZsRuBmBm2XX8MjSvRX9jym9b8jddytWuBmBmxG42Ww1XEU1"
         "/VGwws0I3IzAzWw1XPfFSvvPSnsb0fkR3VdH8914Rpp1X8EKNyNwMwI3m1zDtUZpDXPX4NL+e2pvhV7KnSJwMwI3"
         "y96HRzW9thu9mKTz14IVbkbgZgRuVq2XEvUSSt8DiaTW+FK8l3InCNyMwM1mezdEa/Z2uxmNX6/fTcp4Ku3VHA4f"
         "o+NhGKp+nn74ShG4GYGb2Z5pRjVZx0vfPYx6O9H8c/WGWOFmBG5G4Ga/ybyTd3pzWvEAAAAASUVORK5CYII="),
        ("iVBORw0KGgoAAAANSUhEUgAAAFwAAABLCAYAAAD9POB7AAABcUlEQVR4nO3bzQ7BUBCGYcSOBTeivQNx5eIO1I2w"
         "YM1KohMynfPzlXifnZSjvkzGMa3JBAAAAAAAAAAAAAAAAAAAAACqmJZaqGk299fHXXcqtnYKez7WWOc3G+NN/xmB"
         "ixG42Dz1hbZHHo9d73jbNtKebs9nvz/0ju9226z1PEM/HxUuRuBiBC42uId7PVvN69nr9arqem3bhNZ/osLFCFyM"
         "wMWS9+Hn86X3ONozx+bts719e+rvCipcjMDFCFwsuYd7orOV6OzCY79jcn83pO67LSpcjMDFCFysWg+3vJ5uZxdW"
         "dJ79rahwMQIXI3AxWQ+3++JcXs/32H21t96ba6RJ12ypcDECFyNwscE93PYo28Oi++jcHpw7f4/OVpil/CgCFyNw"
         "seR9uNfTS3sziwk9/1tQ4WIELkbgYtXu2bbXKJfLRe/49Xor+n7RHl/bp9kKFS5G4GIELib7r2LufSfevLn0+rXO"
         "lwoXI3AxAhd7ANzUfJvscgbdAAAAAElFTkSuQmCC"),
    ],
    "lie": [
        ("iVBORw0KGgoAAAANSUhEUgAAAFwAAABLCAYAAAD9POB7AAABY0lEQVR4nO3a0W3CMBSFYVp1ANggEzTZAGWCMipM"
         "gLpBwgTZgG4Az74Pdq5jjnH1f29WIERH1pF1w24HAAAAAAAAAAAAAAAAAAAAAC/xUfsB3kXffz9i1+f5ViSrzxI3"
         "wXoELkbgYs12eKpzLdvB9vvX62/w+cNhH6yHoY/eby12uBiBixG42L/p8K0dbO83TXP093M7nR0uRuBiBC72VfsB"
         "ctnOHMej61zuPceXwg4XI3AxAheTdbi6M+25/F2ww8UIXIzAxV7W4alZh2VnHyl2luHt7HE8Rq+nZim52OFiBC5G"
         "4GLF5uHec7a3021nl77/Vmvn4+xwMQIXI3Cx7HO4952i5e1ky3vuLt3ZudjhYgQuRuBi1d5pemcVtvNTs5DS7PPy"
         "v5RGELgYgYtV6/D7/S9Yp87JqQ6110+nn2C9LEuw7rouWJ/Pl+jv8//wRhG4GIGLVZuHt44ObwSBixG42BNTnWCN"
         "icPtpgAAAABJRU5ErkJggg=="),
        ("iVBORw0KGgoAAAANSUhEUgAAAFwAAABLCAYAAAD9POB7AAABXUlEQVR4nO3a0Y3CMBCEYUAUAB2kAkIHiAqOUqEC"
         "RAeECtIBdMA9eyXibOyMMfq/N4s7E42sYWVYLAAAAAAAAAAAAAAAAAAAAABgFsvSD/At2nb3Hnq96x5Zslrl2ATj"
         "EbgYgYtV2+GxzrVsB9v/v15vwd9vt5tgvd+3g/uNxQkXI3AxAhf7mQ5P7WC73/3eDb7/1E7nhIsRuBiBi61LP8An"
         "3jn7eDzMun8unHAxAhcjcDFZh3s7MzYHW3YutnP5t+CEixG4GIGLzdbhsbuOVKmdHZvbvZ8hY3HCxQhcjMDFst2H"
         "e+fs3J3r3d/el6caez/OCRcjcDECF5s8h3u/U7Rs53l5PwNyd/ZUnHAxAhcjcLFi32mm3nd75/JU9nn5XUolCFyM"
         "wMWKdfjz+QrWsTk51qH29dPpL1j3fR+sm6YJ1ufzZfD9+X14pQhcjMDFit2H144OrwSBixG42D9f9GFynqMjgAAA"
         "AABJRU5ErkJggg=="),
        ("iVBORw0KGgoAAAANSUhEUgAAAFwAAABLCAYAAAD9POB7AAABW0lEQVR4nO3a0Q2CMBSFYTUOoBswgbiBcQIdVScg"
         "biBOwAa6gT73PlAurafW/N9bgxZy0hybymIBAAAAAAAAAAAAAAAAAAAAAF+xLP0Av6Jtd++x633/yJLVKsckmI7A"
         "xQhcrNoOj3WuZTvYfr/rbsHnt9tNMN7v29H5pmKFixG4GIGL/U2Hp3awne9+70fvP7fTWeFiBC5G4GLrUjf27qNj"
         "jsdD0ftPxQoXI3AxAheTdbh33+xl98V2/l/BChcjcDECF/tah8c623o+X8E41umpnR3bt8fOUuZihYsRuBiBi2U7"
         "D/eeTeTuXO/8qft+a+r5OCtcjMDFCFxs9j489WzEdp6X9zcgd2fPxQoXI3AxAhcr9p+m96zCdr53X57KPi/vpVSC"
         "wMUIXKxYh3vPv2Mdaq+fz6dgPAxDMG6aJhhfLtfR+/N+eKUIXIzAxYqdh9eODq8EgYsRuNgHCT1kcpv2ockAAAAA"
         "SUVORK5CYII="),
        ("iVBORw0KGgoAAAANSUhEUgAAAFwAAABLCAYAAAD9POB7AAABW0lEQVR4nO3a0Q2CMBSFYTUOoBswgbiBcQIdVScg"
         "biBOwAa6gT73PlAurafW/N9bgxZy0hybymIBAAAAAAAAAAAAAAAAAAAAAF+xLP0Av6Jtd++x633/yJLVKsckmI7A"
         "xQhcrNoOj3WuZTvYfr/rbsHnt9tNMN7v29H5pmKFixG4GIGL/U2Hp3awne9+70fvP7fTWeFiBC5G4GLrUjf27qNj"
         "jsdD0ftPxQoXI3AxAheTdbh33+xl98V2/l/BChcjcDECF/tah8c623o+X8E41umpnR3bt8fOUuZihYsRuBiBi2U7"
         "D/eeTeTuXO/8qft+a+r5OCtcjMDFCFxs9j489WzEdp6X9zcgd2fPxQoXI3AxAhcr9p+m96zCdr53X57KPi/vpVSC"
         "wMUIXKxYh3vPv2Mdaq+fz6dgPAxDMG6aJhhfLtfR+/N+eKUIXIzAxYqdh9eODq8EgYsRuNgHCT1kcpv2ockAAAAA"
         "SUVORK5CYII="),
        ("iVBORw0KGgoAAAANSUhEUgAAAFwAAABLCAYAAAD9POB7AAABXklEQVR4nO3awQ2CQBCFYTUWoB1QgdiBsQItVSsw"
         "dgBWQAfagZ487BwYFta3rPm/20ZdyMtmnAwsFgAAAAAAAAAAAAAAAAAAAADwE8vcNzAXdb17933eto8kWa1SbILh"
         "CFyMwMWKreFezbVsDba/v93uwfe3202w3u/r3v2G4oSLEbgYgYv9TQ2fWoPtfk3T9l5/bE3nhIsRuBiBi61z38BX"
         "bF9tHY8H6fXG4oSLEbgYgYvJarhXM72+17J9sGX78rnghIsRuBiBi/2shnuzjtRi9/f69tj/lKE44WIELkbgYsnm"
         "4bGzCa/mevPs1PtPNXQ+zgkXI3AxAhcb3YfHPlO0YmuyFdt3p67ZY3HCxQhcjMDFsj3TnDr/jn2GOZW9X95LKQSB"
         "ixG4WLYa/ny+grXXJ3s11H5+Pp+Cddd1wbqqqmB9uVx7r8/74YUicDECF8s2Dy8dNbwQBC5G4GIfv6Rg42yiQ4EA"
         "AAAASUVORK5CYII="),
        ("iVBORw0KGgoAAAANSUhEUgAAAFwAAABLCAYAAAD9POB7AAABYklEQVR4nO3awY3CMBSEYRZRwNJBKiB0gFIBlAoV"
         "IDogW0E6YDuAs9/BLzbOGKP/u1mBJBpZI+vBagUAAAAAAAAAAAAAAAAAAAAAi/ip/QKfou93z9j1cfwrktW6xE0w"
         "H4GLEbhYsx3uda5lO9h+/3q9BZ/fbn+D9X7fR+83FztcjMDFCFzsazr83Q6297vfx+jzczudHS5G4GIELrap/QK5"
         "bGcOwyHpXJ56ji+FHS5G4GIELlatw5fuUHsu/xTscDECFyNwscU63Otob/bhsbOM1M4ehkP0ujdLycUOFyNwMQIX"
         "KzYPTz1Xe53rzbNL3/9dc+fj7HAxAhcjcLHsc3jqb4pWaidbqefu0p2dix0uRuBiBC5WbR6eOquwne/NQkqz78v/"
         "UhpB4GIELlatwx+P/2DtnZO9DrXXT6djsJ6mKVh3XResz+dL9Pn8P7xRBC5G4GLV5uGto8MbQeBiBC72Ahb9YI34"
         "X53nAAAAAElFTkSuQmCC"),
    ],
    "swipe": [
        ("iVBORw0KGgoAAAANSUhEUgAAAFwAAABLCAYAAAD9POB7AAAB6ElEQVR4nO3bQVKDQBCFYbTcmYW5AScQbmDl5Clv"
         "EDwBN4iLuNaVC7rEnmZm3mD5fzuKCgmvpppOA10HAAAAAAAAAGjgrvUPqGUYnj9/2z9Nb03O/b7Fl/5nBC5G4GIP"
         "rX9AKbZmn8+vi/2n00vW8Typ1wRWuBiBixG42J+t4V7NPh6fqh5vHIfQ8b+xwsUIXIzAxVZr+F5nEaV45+f17VvP"
         "nxUuRuBiBC6W3If/MJuoMmso5Xp9X2xfLlPW8bb23RYrXIzAxQhcbPMsJVoTx3FY1PzWfbytyfYaZXnXMObhO0Xg"
         "YgQullxHvXmx5c2jbQ31amD0+6O/xxPtw9fOhxUuRuBiBC6W3IfbmmT70GhNtX186T49t2Zb3v+O1BrPChcjcDEC"
         "F6v2XIqdR+c+J2J59xxz/ydYXo1mlrJTBC5G4GLFZtLRWYetwdE+3hN9HtxTan7PChcjcDECF6t2X9Hro3NrdulZ"
         "iRWd16dihYsRuBiBi1WbpdiaF33v0YrWbDvL8ZTu29ewwsUIXIzAxXbznmZuDbX3HKPHy303PxUrXIzAxQhcTPaM"
         "tu3DD4fHxf7b7aOL7Lf6vl9sz/O82Pb+F0Q/vxUrXIzAxQhcrFkfbmuyV2MTamjue6NZs55UrHAxAhcjcLEvKp6k"
         "p/v4LdEAAAAASUVORK5CYII="),
        ("iVBORw0KGgoAAAANSUhEUgAAAFwAAABLCAYAAAD9POB7AAABrUlEQVR4nO3cMXLCMBSEYSdDF4pwA58g9g0YTs7k"
         "Bjgn8A1IATWpUvgVPD1JXsHwfx3jiWx2NIsilHQdAAAAAAAAAAAAAADAS3hr/QBrGYav273r0/TT5L2/t7jpKyNw"
         "MQIX29QayHamuiPt/Y/H78X1w2FfNJ4n9f0yw8UIXIzAxbI7PKEzV+107/673eeq443jEBr/HzNcjMDFCFwsucNr"
         "d2Zr3jrbW7fnfiYxw8UIXIzAxartpTya8/l38fp0morGy113W8xwMQIXI3Cx1TrcduY4Dk33yy3byfb3CqvWXhEz"
         "XIzAxQhcTLYO9zo9yuvc6PN4vHV46ne6zHAxAhcjcDFZh9u9Dcvr5Oi5ktr7817np+61MMPFCFyMwMWy9zO87zgt"
         "28Gl62iv073xox3vdTR7KQ+KwMUIXKzannT0PHW0w2t3blSt/XtmuBiBixG4WLW9FK/jSs/yeexeR/QzovT+qZjh"
         "YgQuRuBisrMhtsO324/F9cvl2kWuW33fL17P8xx6Pu/nWYc/KQIXI3CxZufDbSfbjsz42/3S/49SdE4mFTNcjMDF"
         "CFzsD+/Bkf5T7OifAAAAAElFTkSuQmCC"),
        ("iVBORw0KGgoAAAANSUhEUgAAAFwAAABLCAYAAAD9POB7AAABh0lEQVR4nO3bQY6CQBCFYZy408V4A04g3MB4cjM3"
         "EE/ADXSh65mViVTiVFfTPEj8vx1BsHzpVDoFVhUAAAAAAAAAAAAAAAAAAAAATGKVe2HT7H9fj7vukn2vKdj6rLnq"
         "/ZrjSz8ZgYsRuNg69YO2J55OP4Pzx+Nh1p6eUN+o+3lSfy8rXIzAxQhc7G0P93ribvc9TUWJStcXvV/bNqH7P7HC"
         "xQhcjMDFkvfhUUudZTx59Xn79tz6WeFiBC5G4GLZPfx6vQ2Oz+cudH3bNqFZRdTY+qzcfbfFChcjcDECF5tsH27Z"
         "nmrZ2YUnOt+2bE/2vr/U/J8VLkbgYgQuljwP8ObFHttz1dePnd9H9+HvejorXIzAxQhcLHkfbnuS3YcuTelnrt4s"
         "JrXHs8LFCFyMwMVkzxVLv/vn8fbp0R7v9WhmKQtF4GIELjZbD99uN4Pz9/ujipy36roeHPd9H6zwf6Xeo2GFixG4"
         "GIGLyZ5pWrYn2x6Z8T/QUe8yRv/Tk4sVLkbgYgQu9gfQgYOUhAzeAwAAAABJRU5ErkJggg=="),
        ("iVBORw0KGgoAAAANSUhEUgAAAFwAAABLCAYAAAD9POB7AAABvklEQVR4nO3cwW3CQBCFYYi4hUNoJKaDiApCBxGV"
         "onSAqcAdkA6SE0geJZkd7/LsNf93sxDO8rSajIY1iwUAAAAAAKjYcuwF3EvTvH7/93rbnkf57E9j/NFHRuBiBC62"
         "GnsBpdiafTx+9l7f7d6y7udJ/Z/ADhcjcDECF6u2hns1e7N5uev9ttsmdP8rdrgYgYsRuFi1NTyX12d7ffvQWQw7"
         "XIzAxQhcbLY1/HL56l2fTm3W/Yb23RY7XIzAxQhcbLY13GNrsp2dWL/M13t9PPPwiSJwMQIXq+Zcijev9kTn41a0"
         "D/+rprPDxQhcjMDFZtuH59Zsy5vFpNZ4drgYgYsRuFi1fbjH69OjNd6r0cxSJorAxQhcrFgNL32eOnd2Ej0P7in1"
         "TBA7XIzAxQhcLLkueTU6eu7D62vVfXTuM0H04RNF4GIELnabh0drtD27l6t0zbbs+vf79961rdl2PYfDR++667pB"
         "62CHixG4GIGLLa+1O/qcY7SGezXS462n1PntVDzjUwkCFyNwsVsfXnp+bK3Xz1nvz5292M/Hb149CAIXI3AxWR2L"
         "fudpRb8Djb5fhR0uRuBiBA4AQKIfpm+B24rQh2wAAAAASUVORK5CYII="),
        ("iVBORw0KGgoAAAANSUhEUgAAAFwAAABLCAYAAAD9POB7AAABgklEQVR4nO3awW3CQBCFYYi4hUNoBNNBRAXQQUSl"
         "KB1gKnAHpAM4gbSjhPGw9rPX+b+bZbRenlbDaPBsBgCdmQ+9gb5U1fr67H5dnwf57m9DPPQ/I3AxAhdbDL2Brtia"
         "fTx+J/e328+s9TxtfxM44WIELkbgYsXWcK9mr1Yfva632VSh9e844WIELkbgYsXW8Fxen+317a/OYjjhYgQuRuBi"
         "k63hl8tPcn061Vnrvdp3W5xwMQIXI3CxydZwj63JdnZi/TJfT/p45uEjReBiBC5WzHsp3rzaE52PW9E+/K+azgkX"
         "I3AxAhfrrA+PvsfRt9yabXmzmLY1nhMuRuBiBC7Wug/3anR03hydZVjef47eetEa79VoZikjReBiBC726MOjNdr+"
         "Z+jJrdnefrznjQUnXIzAxQhcbHGv3bnvV9uabvvk5fI9vruM/Xg1fr/fJddN0yTXNo/D4evp59vihIsRuBiBi83H"
         "NscuBe+HF4LAxQgcAAAAAAAAAAAAAAAAmIAb3SlmhZnOsVQAAAAASUVORK5CYII="),
        ("iVBORw0KGgoAAAANSUhEUgAAAFwAAABLCAYAAAD9POB7AAABn0lEQVR4nO3b0W3CMBDGcVr1rTyUDTJBkw1QJqmY"
         "FHUD0gmyAd2gfQLJJ9HDPvM50P/vLQKc8Mm6mItZrQAAAAAAAAAAAABkeGp9AbfS9+8/f70+TV9Nvvtzi5P+ZwQu"
         "RuBiL60voBZbs/f7z+T1cdyGxvNce09ghosRuBiBi91tDfdq9mbzdtPxhqHPGv+EGS5G4GIELnaxhueuQ3O16mWc"
         "eN/PW7eXXj8zXIzAxQhc7FzDa69rPcPQJ+erXdOPx+/k+HCYQuOVrrstZrgYgYsRuNi5buauu21NtDUzt+ZHa6S9"
         "51heL8T7vGXX6fTDF4rAxQhcrHjt69V8rybaGlj7/Vb0d0TuPeZSTWeGixG4GIGLFT/T9Nad47gN1fio2r0frxdz"
         "bY1nhosRuBiBi8n2pazXr6HP2xoa7b3k9se989FLWSgCFyNwMdnekOg+l+gzSduvz90vbrEv5U4QuBiBi8nW4dF9"
         "J3YfSy57D+i6Ljme5zk5tr2e3e7DDlm0r4YZLkbgYgQu9rD/tbeWst+dGS5G4GIEDgAAAODh/QJFLXmQRhaCLgAA"
         "AABJRU5ErkJggg=="),
        ("iVBORw0KGgoAAAANSUhEUgAAAFwAAABLCAYAAAD9POB7AAABkElEQVR4nO3aQW7CMBSE4bTqrizKRZrcoOIkFSdF"
         "vQHhBLkBLOi6XSE1TxVjO85AxP/tooAxI+thXtw0AAAAAAAAAAAAAAAAAADctadaA7Xt+8/f674/VBu7RJxPdKv5"
         "Pd/iQx8ZgZsRuNlL6Rtjjdztvkb3N5sPa01PmM+k8ZTU78cKNyNwMwI3S67hqkau1291ZpSo9nxyx+u6Nmv8C1a4"
         "GYGbEbhZ8T586dQ+W+3bS/9XsMLNCNyMwM1mq+H7fT+67rrW2ls5Hk9X55OrdN8dscLNCNyMwM1s+3BV0x8FK9yM"
         "wM0I3MxWw+O+OIr95yj2NtTrlbivVuPVembLCjcjcDMCN0uu4bFGxRrmrsGKeqaZ21uhl7JQBG5G4GbF+3BV02v7"
         "pxdz9fXqN8J9juaCFW5G4GYEblatl6J6CVPPgSi5NX4qzqUsBIGbEbjZbGdDYs1erV5H98/n7ybnfq64D99uP0fX"
         "wzBUfT/98DtF4GYEbmZ7pqlqcrw/9eyh6u2o8efqDbHCzQjcjMDNfgGzB5B3yTlmTAAAAABJRU5ErkJggg=="),
        ("iVBORw0KGgoAAAANSUhEUgAAAFwAAABLCAYAAAD9POB7AAABdElEQVR4nO3bwU7CQBCHcTTe5CAvYvsGhicnvgH1"
         "RfCAZz2R2Il2utvth8TvdyPIsv4zGYZt2WwkSZIkSZIkSZIkSZIkSZIkaRV3rRbquufP74+H4a3Z2jXifqJr7e/+"
         "Gm/6nxk4zMBhD7UvjD3ycHgdPb/fv6A9fcZ+Fq2Xmfv/WeEwA4cZOGx2D8965G731GZHM7XeT+l6fd8VrX9hhcMM"
         "HGbgsOo5/NZlc3Y2t9d+r7DCYQYOM3DYaj38eBxGj/u+mzxbKT27yJxO75P7KVU7d0dWOMzAYQYOw+bwrKfHs4uo"
         "9Dz7r7LCYQYOM3AY1sPjXLxU1vMzca7O1mt1zdYKhxk4zMBhs3t47FGxh5XO0Ut7cCa7pll6tuJZyo0ycJiBw6rn"
         "8Kynt/bDWczk32efEfR9NBdWOMzAYQYOW+2e7XiNcrt9HD1/Pn80fb/SHr+2385WrHCYgcMMHIb9VnHpfSfZeXPr"
         "9dfarxUOM3CYgcO+ABMteZsX1LrnAAAAAElFTkSuQmCC"),
        ("iVBORw0KGgoAAAANSUhEUgAAAFwAAABLCAYAAAD9POB7AAABl0lEQVR4nO3aMW6DQBSEYRKli4v4IoEbRD5J5JNa"
         "uYHJCbiBXTh1UqXgyWZYdhmw/H8dWljDaPX0vFBVAAAAAAAAAAAAAAAAAACs2tOtgbp+/x26sG2/b167Bmu9/+cl"
         "fvSREbgZgZu9jD3xcPjqHe92H70auXRNjzX7yv1mzaeMfX5WuBmBmxG42egaHh2Pbe+4aWprTVc1e7t9m3W+pqmT"
         "5v/HCjcjcDMCN5tcw6Ola3oq1Wervn3q87DCzQjcjMDNRteh3L439q25NV3dT5Tal0el7p8VbkbgZgRuVqwPV1Sf"
         "/ihY4WYEbkbgZrYafjqdB8dVHx33NtT5Suyr1Xyl3umyws0I3IzAzUbX8FijYg1z12BF7Z3E/wXK1HeYESvcjMDN"
         "CNxsch+uanppV/ZiBs+fe398Kla4GYGbEbhZsb0UtZeQ+x2Iklrjc/FO804QuBmBm832vV+s2ZvNa2/8cvmpUsZT"
         "xT58v//sHXddV/R69sNXisDNCNzM9k5T1eQ4nvvtodrbUfPPtTfECjcjcDMCN/sDX4+ZkxogJdoAAAAASUVORK5C"
         "YII="),
        ("iVBORw0KGgoAAAANSUhEUgAAAFwAAABLCAYAAAD9POB7AAABsklEQVR4nO3bQW7CMBCF4bTqrizKRZrcoOIkFSdF"
         "3ID0BLkBXdB1u8rCI2AyjvPiiv/bRQGTPFkTa2KaBgAAAAAAAAAAAAAA4CE8rX0BS2nb99975/v+a5V7f17jRx8Z"
         "gYsRuNjL2hdQiq3Zh8MxOb/bfcwazzP1mcAMFyNwMQIXu1nDa13Hjryavd2+LTpe17Wh8UfMcDECFyNwscnr8Cvr"
         "2qTmrV3To7xnlLduz71fZrgYgYsRuFh2L+V06pPjrmurqunn83dybK83KnfdbTHDxQhcjMDFivXDa6/ptWCGixG4"
         "GIGL3ayrXn/Y8vrPpdaxI+96LK+fHR3P9lp4p1kpAhcjcLHJa+O57xBtb8PWQK+GRj8ffafp8Z5B1PBKEbgYgYsV"
         "66XYGm1Fa7B1pVdz9/PqGj8VM1yMwMUIXCy7Rx3dP23N7YV4SvduLPal/BMELkbgYtnr8GgNm7uXz+PtO4n2fpZ6"
         "BjDDxQhcjMDFFtsrYmv2ZvOanL9cfprI+Shbs/f7z+R4GIai36cfXikCFyNwMdl/7b2abM/P3Yto/4NkeeN738/F"
         "DBcjcDECF/sDtUmVBgG0ihQAAAAASUVORK5CYII="),
        ("iVBORw0KGgoAAAANSUhEUgAAAFwAAABLCAYAAAD9POB7AAAByElEQVR4nO3bTU7CYBDGcTTuZCE36Alsb2A4OfEG"
         "1BP0BrjAta4a806E6bwfT5v4/+2aYilPJsM4wG4HAAAAAAAAAAAAIOBh7Rtope9fv++dH8ePVV774xpP+p8RuBiB"
         "iz2tfQO12J59Or0n54/Ht6LreZa+J1DhYgQuRuBiN3v4VufYmdezD4eXptcbhj50/RkVLkbgYgQutngO/2OubTKn"
         "qnjvUd7cnvt6qHAxAhcjcLHsXcr5PIYePwx90jNb9/TL5TM5jt6vlTt3W1S4GIGLEbjYzR5ue6ydu+1cbtndg+2h"
         "6p6+FVS4GIGLEbhYdt+svY+2c67t6d7zebx9dvR6dtfCZ5obReBiBC7W7HspdpdR+hljlPd8Gbuggrv5RYWLEbgY"
         "gYtl9/DorsX2dDvHls7BVnTXo0KFixG4GIGLNdtBe3N0tGdbXg+uNTfPau3rqXAxAhcjcLFmuxRvnx0VnZtrz/W1"
         "UOFiBC5G4GKb+Z1maQ+1++3o9Up/17kUFS5G4GIELib7Pp+dw/f75+T89fq1i5y3uq5LjqdpSo69/wuif5+LChcj"
         "cDECF1ttDrc92euxC3po6e9Gi3Y9S1HhYgQuRuBiP8zinT9mNpxfAAAAAElFTkSuQmCC"),
    ],
}


def load_settings():
    cfg = json.loads(json.dumps(DEFAULTS))
    try:
        with open(SETTINGS_FILE, "r", encoding="utf-8") as f:
            cfg.update(json.load(f))
    except Exception:
        pass
    return cfg


def save_settings(cfg):
    try:
        with open(SETTINGS_FILE, "w", encoding="utf-8") as f:
            json.dump(cfg, f, ensure_ascii=False, indent=2)
    except Exception:
        pass


def work_area(root):
    if IS_WIN:
        try:
            import ctypes
            from ctypes import wintypes
            r = wintypes.RECT()
            ctypes.windll.user32.SystemParametersInfoW(48, 0, ctypes.byref(r), 0)
            return r.left, r.top, r.right, r.bottom
        except Exception:
            pass
    return 0, 0, root.winfo_screenwidth(), root.winfo_screenheight()


class XShape:
    """Linux/X11: recorta la ventana a rectángulos (transparente y sin bloquear clics)."""

    def __init__(self, root, width, height):
        import ctypes
        import ctypes.util
        self.ct = ctypes
        x11, xext = ctypes.util.find_library("X11"), ctypes.util.find_library("Xext")
        if not x11 or not xext:
            raise RuntimeError("faltan libX11/libXext")
        self.x11, self.xext = ctypes.CDLL(x11), ctypes.CDLL(xext)
        c_void_p, c_ulong, c_int = ctypes.c_void_p, ctypes.c_ulong, ctypes.c_int

        class XRect(ctypes.Structure):
            _fields_ = [("x", ctypes.c_short), ("y", ctypes.c_short),
                        ("width", ctypes.c_ushort), ("height", ctypes.c_ushort)]
        self.XRect = XRect
        self.x11.XOpenDisplay.restype = c_void_p
        self.x11.XOpenDisplay.argtypes = [ctypes.c_char_p]
        self.x11.XFlush.argtypes = [c_void_p]
        self.x11.XQueryTree.argtypes = [c_void_p, c_ulong, ctypes.POINTER(c_ulong),
                                        ctypes.POINTER(c_ulong),
                                        ctypes.POINTER(ctypes.POINTER(c_ulong)),
                                        ctypes.POINTER(ctypes.c_uint)]
        self.x11.XFree.argtypes = [c_void_p]
        self.xext.XShapeQueryExtension.argtypes = [c_void_p, ctypes.POINTER(c_int),
                                                   ctypes.POINTER(c_int)]
        self.xext.XShapeCombineRectangles.argtypes = [c_void_p, c_ulong, c_int, c_int, c_int,
                                                      ctypes.POINTER(XRect), c_int, c_int, c_int]
        self.dpy = self.x11.XOpenDisplay(None)
        if not self.dpy:
            raise RuntimeError("sin display X11")
        a, b = c_int(), c_int()
        if not self.xext.XShapeQueryExtension(self.dpy, ctypes.byref(a), ctypes.byref(b)):
            raise RuntimeError("sin extensión SHAPE")
        root.update_idletasks()
        wid = root.winfo_id()
        self.wids = [wid]
        rt, par, kids, n = c_ulong(), c_ulong(), ctypes.POINTER(c_ulong)(), ctypes.c_uint()
        if self.x11.XQueryTree(self.dpy, wid, ctypes.byref(rt), ctypes.byref(par),
                               ctypes.byref(kids), ctypes.byref(n)):
            if kids:
                self.x11.XFree(kids)
            if par.value and par.value != rt.value:
                self.wids.append(par.value)
        self.w, self.h = width, height
        self.last = None

    def set(self, rects):
        key = tuple(rects)
        if key == self.last:
            return
        self.last = key
        out = []
        for x, y, w, h in rects:
            x0, y0 = max(0, int(x)), max(0, int(y))
            x1, y1 = min(self.w, int(x + w)), min(self.h, int(y + h))
            if x1 > x0 and y1 > y0:
                out.append(self.XRect(x0, y0, x1 - x0, y1 - y0))
        arr = (self.XRect * max(1, len(out)))(*out) if out else (self.XRect * 1)(self.XRect(0, 0, 1, 1))
        n = len(out) if out else 1
        for wid in self.wids:
            for kind in (0, 2):                    # ShapeBounding, ShapeInput
                self.xext.XShapeCombineRectangles(self.dpy, wid, kind, 0, 0, arr, n, 0, 0)
        self.x11.XFlush(self.dpy)


class Fox:
    def __init__(self):
        if IS_WIN:
            try:
                import ctypes
                ctypes.windll.shcore.SetProcessDpiAwareness(1)
            except Exception:
                pass
        self.cfg = load_settings()
        self.z = max(1, min(5, int(round(float(self.cfg["zoom"])))))
        self.root = tk.Tk()
        self.root.title("Zorro ártico")
        self.root.withdraw()
        self.root.overrideredirect(True)
        self.sw, self.sh = self.root.winfo_screenwidth(), self.root.winfo_screenheight()

        # --- caché de imágenes
        self.raws, self.imgs, self.runs = {}, {}, {}
        self.shape = None
        self.mode = "compact"
        self.bg = "#C9D6E2"
        self.c = tk.Canvas(self.root, highlightthickness=0, bd=0)
        self.c.pack()
        self.setup_overlay()
        self.c.config(bg=self.bg)
        self.root.config(bg=self.bg)
        self.full = self.mode != "compact"
        self.apply_size()
        if self.mode == "shape":
            try:
                self.shape = XShape(self.root, self.cw, self.ch)
                self.shape.set([(0, 0, 1, 1)])
            except Exception as e:
                print("Modo compacto (sin SHAPE):", e)
                self.mode, self.full, self.bg = "compact", False, "#C9D6E2"
                self.c.config(bg=self.bg)
                self.root.config(bg=self.bg)
                self.apply_size()
        try:
            self.root.attributes("-topmost", True)
        except tk.TclError:
            pass
        self.root.deiconify()

        l, t, r, b = work_area(self.root)
        self.x, self.y = r - 300, b - 120
        self.ox = self.oy = 0
        self.face = 1
        self.t = 0
        self.moving = False
        self.walked = 0.0
        self.lock_face = False
        self.state = "idle"
        self.tx = self.ty = 0
        self.queue = []
        self.mud_until = 0
        self.prints = collections.deque()
        self.print_flat, self.print_ver, self.print_seen = [], 0, -1
        self.print_side = 1
        self.mx = self.my = 0
        self.anim, self.anim_t0 = "idle", time.time()
        self.swipe_until = 0
        self.left = self.top = 0
        self.cur_img = None
        self.item = self.c.create_image(0, 0, anchor="nw", tags="fox")
        self.next_idle = time.time() + 2
        self.next_special = time.time() + 15
        self.sleep_until = 0
        self.grab_t = self.pull_end = self.chase_t = 0
        self.wins = []
        self.carry = None
        self.pending = None
        self.last_click = 0
        self.single_job = None
        self.pressing = False
        self.moved = False
        self.settings_win = None

        self.c.bind("<ButtonPress-1>", self.on_press)
        self.c.bind("<B1-Motion>", self.on_motion)
        self.c.bind("<ButtonRelease-1>", self.on_release)
        self.c.bind("<Button-3>", self.show_menu)
        if IS_MAC:
            self.c.bind("<Button-2>", self.show_menu)
        self.build_menu()
        self.yip()
        self.tick()

    # ---------------------------------------------------------- ventana
    def setup_overlay(self):
        if "--compacto" in sys.argv:
            return
        try:
            if IS_WIN:
                self.root.attributes("-transparentcolor", KEY)
                self.mode, self.bg = "color", KEY
            elif IS_MAC:
                self.root.attributes("-transparent", True)
                self.mode, self.bg = "alpha", "systemTransparent"
            else:
                self.mode, self.bg = "shape", KEY
        except tk.TclError:
            self.mode, self.bg = "compact", "#C9D6E2"

    def apply_size(self):
        z = self.z
        if self.full:
            self.cw, self.ch = self.sw, (self.sh - 1 if IS_WIN else self.sh)
            self.root.geometry("%dx%d+0+0" % (self.cw, self.ch))
        else:
            self.cw, self.ch = int(150 * z), int(130 * z)
        self.c.config(width=self.cw, height=self.ch)

    def set_zoom(self):
        self.z = max(1, min(5, int(round(float(self.cfg["zoom"])))))
        self.imgs.clear()
        self.clear_prints()
        self.apply_size()

    def save(self, key, val):
        self.cfg[key] = val
        save_settings(self.cfg)

    # ---------------------------------------------------------- sprites
    def raw(self, anim, idx):
        key = (anim, idx)
        if key not in self.raws:
            self.raws[key] = tk.PhotoImage(data=FRAMES[anim][idx])
        return self.raws[key]

    def get_img(self, anim, idx, flip):
        key = (anim, idx, flip, self.z)
        if key not in self.imgs:
            src = self.raw(anim, idx)
            if flip:
                fl = tk.PhotoImage()
                self.root.tk.call(fl, "copy", src, "-subsample", -1, 1)
                src = fl
            self.imgs[key] = src.zoom(self.z) if self.z > 1 else src
        return self.imgs[key]

    def sprite_runs(self, anim, idx):
        """Rectángulos opacos del fotograma (para la forma de la ventana en Linux)."""
        key = (anim, idx)
        if key not in self.runs:
            img = self.raw(anim, idx)
            rows = []
            for y in range(FH):
                runs, x = [], 0
                while x < FW:
                    if img.transparency_get(x, y):
                        x += 1
                        continue
                    x0 = x
                    while x < FW and not img.transparency_get(x, y):
                        x += 1
                    runs.append((x0, x))
                rows.append(tuple(runs))
            rects, y = [], 0
            while y < FH:
                y2 = y
                while y2 + 1 < FH and rows[y2 + 1] == rows[y]:
                    y2 += 1
                rects += [(x0, y, x1 - x0, y2 - y + 1) for x0, x1 in rows[y]]
                y = y2 + 1
            self.runs[key] = rects
        return self.runs[key]

    # ---------------------------------------------------------- utilidades
    def yip(self):
        if not self.cfg["sound"]:
            return
        if IS_WIN:
            def f():
                try:
                    import winsound
                    winsound.Beep(1000, 55)
                    winsound.Beep(1450, 85)
                except Exception:
                    pass
            threading.Thread(target=f, daemon=True).start()
        else:
            try:
                self.root.bell()
            except Exception:
                pass

    def set_cursor(self, x, y):
        if IS_WIN:
            try:
                import ctypes
                ctypes.windll.user32.SetCursorPos(int(x), int(y))
            except Exception:
                pass

    def corner(self):
        l, t, r, b = work_area(self.root)
        return r - 50 * self.z, b - 36 * self.z

    def bounds(self):
        l, t, r, b = work_area(self.root)
        z = self.z
        return l + 46 * z, t + 38 * z, r - 46 * z, b - 36 * z

    # ---------------------------------------------------------- ratón
    def hit(self, e):
        img = self.cur_img
        if img is None:
            return False
        lx, ly = e.x - self.left, e.y - self.top
        return (0 <= lx < img.width() and 0 <= ly < img.height()
                and not img.transparency_get(int(lx), int(ly)))

    def on_press(self, e):
        self.pressing = self.hit(e)
        if not self.pressing:
            return
        self.press = (e.x_root, e.y_root)
        self.off = (e.x_root - self.x, e.y_root - self.y)
        self.moved = False

    def on_motion(self, e):
        if not self.pressing:
            return
        if not self.moved:
            if math.hypot(e.x_root - self.press[0], e.y_root - self.press[1]) < 5:
                return
            self.moved = True
            self.release_all()
            self.state = "drag"
            self.yip()
        self.x = e.x_root - self.off[0]
        self.y = e.y_root - self.off[1]

    def on_release(self, e):
        if not self.pressing:
            return
        self.pressing = False
        now = time.time()
        if self.moved:
            self.state, self.next_idle = "idle", now + 2
            return
        if now - self.last_click < 0.35:
            if self.single_job:
                self.root.after_cancel(self.single_job)
                self.single_job = None
            self.last_click = 0
            self.go_corner()
        else:
            self.last_click = now
            self.single_job = self.root.after(360, self.single_click)

    def single_click(self):
        self.single_job = None
        self.yip()
        if self.state == "idle":
            self.swipe_until = time.time() + 1.4

    def release_all(self):
        self.carry = None
        self.lock_face = False
        self.queue = []
        if self.pending:
            try:
                self.pending["win"].destroy()
            except Exception:
                pass
            self.pending = None

    # ---------------------------------------------------------- acciones
    def go_corner(self):
        self.release_all()
        self.tx, self.ty = self.corner()
        self.state = "run"
        self.yip()

    def go_sleep(self):
        self.face = -1
        self.state = "sleep"
        self.sleep_until = time.time() + float(self.cfg["sleep_min"]) * 60

    def start_wander(self):
        x0, y0, x1, y1 = self.bounds()
        self.tx, self.ty = random.uniform(x0, x1), random.uniform(y0, y1)
        self.state = "walk"

    def start_mud(self):
        if not self.full:
            return
        x0, y0, x1, y1 = self.bounds()
        self.queue = [(random.uniform(x0, x1), random.uniform(y0, y1)) for _ in range(3)]
        self.mud_until = time.time() + 40
        self.tx, self.ty = self.queue.pop(0)
        self.state = "walk"

    def start_chase(self):
        if not IS_WIN:
            return
        self.state, self.chase_t = "chase", time.time()
        self.yip()

    def start_bring(self, kind):
        self.wins = [w for w in self.wins if w.winfo_exists()]
        if len(self.wins) >= 5 or self.state == "sleep":
            return
        win, w, h = self.make_window(kind)
        side = random.choice([-1, 1])            # -1 = entra por la izquierda
        off_x = -(w + 330) if side == -1 else self.sw + w + 330
        self.pending = {"win": win, "w": w, "h": h, "side": side}
        self.tx, self.ty = off_x, random.uniform(h / 2 + 80, self.sh - h / 2 - 140)
        self.state = "bring_go"

    def choose(self, now):
        c, f = self.cfg, self.cfg["freq"]
        sp = []
        if now >= self.next_special:
            if c["steal"] and IS_WIN:
                sp.append("chase")
            if c["notes"]:
                sp.append("note")
            if c["memes"]:
                sp.append("meme")
            if c["prints"] and self.full:
                sp.append("mud")
        if sp and random.random() < 0.6:
            act = random.choice(sp)
            self.next_special = now + random.uniform(25, 70) / f
            {"chase": self.start_chase, "mud": self.start_mud,
             "note": lambda: self.start_bring("note"),
             "meme": lambda: self.start_bring("meme")}[act]()
            return
        r = random.random()
        if r < 0.6 and c["wander"]:
            self.start_wander()
        elif r < 0.75:
            self.swipe_until = now + 1.4
            self.yip()
        self.next_idle = now + random.uniform(1.5, 5)

    def move(self, tx, ty, sp):
        dx, dy = tx - self.x, ty - self.y
        d = math.hypot(dx, dy)
        if d <= sp:
            self.x, self.y = tx, ty
            return True
        self.x += dx / d * sp
        self.y += dy / d * sp
        if abs(dx) > 1 and not self.lock_face:
            self.face = 1 if dx > 0 else -1
        self.moving = True
        self.walked += sp
        if self.mud_until > time.time() and self.cfg["prints"] and self.full:
            if self.walked >= 20 * self.z:
                self.walked = 0
                self.add_print(math.atan2(dy, dx))
        return False

    # ---------------------------------------------------------- huellas (pixel art)
    def add_print(self, ang):
        z = self.z
        self.print_side *= -1
        ca, sa = math.cos(ang), math.sin(ang)
        px = self.x - self.face * 8 * z - sa * 4 * z * self.print_side
        py = self.y + 30 * z + ca * 3 * z * self.print_side

        u = 3 * z                            # tamaño del "píxel" de la huella

        def at(lx, ly, w, h):
            cx = round((px + (lx * ca - ly * sa) * u) / u) * u
            cy = round((py + (lx * sa + ly * ca) * u) / u) * u
            return (int(cx - w * u / 2), int(cy - h * u / 2), int(w * u), int(h * u))
        horiz = abs(ca) > 0.7
        rects = [at(0, 0, 3 if horiz else 2, 2 if horiz else 3)]
        for lx, ly in ((3, -2), (4, 0), (3, 2)):
            rects.append(at(lx, ly, 1, 1))
        ids = [self.c.create_rectangle(x, y, x + w, y + h, fill=self.cfg["mud"],
                                       outline="", tags="fp") for x, y, w, h in rects]
        self.prints.append((time.time(), ids, rects))
        self.print_ver += 1
        self.c.tag_lower("fp")

    def clear_prints(self):
        self.c.delete("fp")
        self.prints.clear()
        self.print_ver += 1

    # ---------------------------------------------------------- bucle
    def tick(self):
        now = time.time()
        self.t += 1
        self.moving = False
        st, sp = self.state, float(self.cfg["speed"])
        sf = self.z / 2
        cx, cy = self.root.winfo_pointerxy()
        z = self.z

        if st == "sleep":
            if now >= self.sleep_until:
                self.state, self.next_idle = "idle", now + 2
                self.yip()
        elif st == "idle":
            if now >= self.next_idle:
                self.choose(now)
        elif st == "walk":
            if self.move(self.tx, self.ty, sp * 0.55 * sf):
                if self.queue:
                    self.tx, self.ty = self.queue.pop(0)
                else:
                    self.state, self.next_idle = "idle", now + random.uniform(1.5, 5)
        elif st == "run":
            if self.move(self.tx, self.ty, sp * 1.9 * sf):
                self.go_sleep()
        elif st == "chase":
            ft = 1 if cx > self.x else -1
            if self.move(cx - ft * 36 * z, cy + 3 * z, sp * 1.9 * sf) \
                    or math.hypot(cx - self.mx, cy - self.my) < 22 * z:
                self.state, self.grab_t = "grab", now
            elif now - self.chase_t > 12:
                self.state, self.next_idle = "idle", now + 3
        elif st == "grab":
            if math.hypot(cx - self.mx, cy - self.my) > 90 * z:
                self.state, self.chase_t = "chase", now
            elif now - self.grab_t > 0.6:
                x0, y0, x1, y1 = self.bounds()
                for _ in range(12):
                    self.tx, self.ty = random.uniform(x0, x1), random.uniform(y0, y1)
                    if math.hypot(self.tx - self.x, self.ty - self.y) > 350:
                        break
                self.state, self.pull_end = "pull", now + 5
                self.yip()
        elif st == "pull":
            if self.move(self.tx, self.ty, sp * 0.8 * sf) or now > self.pull_end:
                self.yip()
                self.start_wander()
        elif st == "bring_go":
            if self.move(self.tx, self.ty, sp * 1.9 * sf):
                self.begin_carry()
        elif st == "bring_carry":
            if self.move(self.tx, self.ty, sp * 0.8 * sf):
                self.end_carry()

        self.mx = self.x + self.face * 36 * z
        self.my = self.y - 3 * z
        self.after_move()
        while self.prints and now - self.prints[0][0] > self.cfg["print_secs"]:
            for i in self.prints.popleft()[1]:
                self.c.delete(i)
            self.print_ver += 1
        if self.t % 90 == 0:
            try:
                self.root.lift()
            except tk.TclError:
                pass
        self.draw(now)
        self.root.after(FPS_MS, self.tick)

    def after_move(self):
        z, f = self.z, self.face
        if self.state == "pull":
            self.set_cursor(self.mx + f * 4 * z, self.my)
        elif self.state == "bring_carry" and self.carry:
            win = self.carry["win"]
            if not win.winfo_exists():
                self.carry = None
                self.lock_face = False
                self.start_wander()
                return
            wx = self.mx if f == 1 else self.mx - self.carry["w"]
            win.geometry("+%d+%d" % (wx, self.my - self.carry["h"] / 2))
            if self.t % 6 == 0:
                self.root.lift()

    # ---------------------------------------------------------- notas / memes
    def load_meme(self):
        folders = [os.path.join(HERE, "memes"), os.path.join(os.path.expanduser("~"), "zorro_memes")]
        files = []
        for d in folders:
            if os.path.isdir(d):
                files += [os.path.join(d, n) for n in os.listdir(d)
                          if n.lower().endswith((".png", ".gif", ".jpg", ".jpeg"))]
        random.shuffle(files)
        for path in files:
            try:
                try:
                    from PIL import Image, ImageTk
                    im = Image.open(path)
                    im.thumbnail((380, 380))
                    return ImageTk.PhotoImage(im)
                except ImportError:
                    img = tk.PhotoImage(file=path)
                    while img.width() > 420 or img.height() > 420:
                        img = img.subsample(2, 2)
                    return img
            except Exception:
                continue
        return None

    def make_window(self, kind):
        win = tk.Toplevel(self.root)
        win.withdraw()
        try:
            win.attributes("-topmost", True)
        except tk.TclError:
            pass
        win.resizable(False, False)
        win.protocol("WM_DELETE_WINDOW", win.destroy)
        if kind == "meme":
            win.title("meme")
            img = self.load_meme() if self.cfg["memes"] else None
            if img:
                lab = tk.Label(win, image=img, bd=0)
                lab.image = img
                lab.pack()
            else:
                col = random.choice(["#BFE3F5", "#FDE4C8", "#E3D5F5", "#D5F5DC"])
                cv = tk.Canvas(win, width=320, height=230, bg=col, highlightthickness=0)
                cv.create_text(160, 80, text="🦊", font=("Segoe UI Emoji", 50))
                cv.create_text(160, 165, text=random.choice(CAPTIONS), width=290,
                               font=("Impact", 22), fill="#222")
                cv.pack()
            tk.Button(win, text="Vale", command=win.destroy).pack(fill="x")
        else:
            win.title("Nota del zorro")
            bg = self.cfg["note_bg"]
            win.configure(bg=bg)
            msgs = self.cfg["messages"] or ["yip"]
            tk.Label(win, text=random.choice(msgs), bg=bg, fg="#333333", wraplength=260,
                     font=("Segoe Print" if IS_WIN else "Helvetica", 13),
                     padx=20, pady=18, justify="left").pack()
            tk.Button(win, text="Vale", command=win.destroy).pack(pady=(0, 10))
        win.update_idletasks()
        return win, win.winfo_reqwidth() + 16, win.winfo_reqheight() + 40

    def begin_carry(self):
        p, self.pending = self.pending, None
        if not p or not p["win"].winfo_exists():
            self.start_wander()
            return
        z = self.z
        self.carry = p
        self.wins.append(p["win"])
        self.face = -p["side"]               # camina hacia dentro empujando la ventana
        self.lock_face = True
        w, h = p["w"], p["h"]
        wx = random.uniform(30, max(31, self.sw - w - 30))
        self.tx = wx - 36 * z if self.face == 1 else wx + w + 36 * z
        self.ty = max(h / 2 + 40, min(self.sh - h / 2 - 90, self.ty))
        self.y = self.ty
        self.state = "bring_carry"
        p["win"].deiconify()
        self.yip()

    def end_carry(self):
        self.carry = None
        self.lock_face = False
        self.yip()
        self.start_wander()

    # ---------------------------------------------------------- dibujo
    def pick_anim(self, now):
        st = self.state
        if st == "sleep":
            return "lie"
        if st in ("run", "chase", "bring_go", "drag"):
            return "run"
        if st == "grab":
            return "swipe"
        if st in ("walk", "pull", "bring_carry"):
            return "walk"
        return "swipe" if now < self.swipe_until else "idle"

    def draw(self, now):
        z, c = self.z, self.c
        anim = self.pick_anim(now)
        if anim != self.anim:
            self.anim, self.anim_t0 = anim, now
        n = len(FRAMES[anim])
        idx = int((now - self.anim_t0) / ANIM_DT) % n
        flip = self.face == -1
        img = self.get_img(anim, idx, flip)
        self.cur_img = img
        if not self.full:
            self.ox = int(self.x - self.cw / 2)
            self.oy = int(self.y - self.ch / 2)
            self.root.geometry("%dx%d+%d+%d" % (self.cw, self.ch, self.ox, self.oy))
        self.left = int(self.x - self.ox - FW * z / 2)
        self.top = int(self.y - self.oy - FH * z / 2)
        c.coords(self.item, self.left, self.top)
        c.itemconfig(self.item, image=img)

        zr = self.draw_zzz(now) if self.state == "sleep" else []
        if not self.state == "sleep":
            c.delete("z")
        if self.shape:
            rects = [(self.left + (FW - x - w if flip else x) * z, self.top + y * z, w * z, h * z)
                     for x, y, w, h in self.sprite_runs(anim, idx)]
            rects += zr
            if self.print_seen != self.print_ver:
                self.print_flat = [r for p in self.prints for r in p[2]]
                self.print_seen = self.print_ver
            self.shape.set(rects + self.print_flat)
        c.tag_raise("fox")

    def draw_zzz(self, now):
        z, out = self.z, []
        self.c.delete("z")
        for i in range(3):
            ph = (now * 0.3 + i / 3) % 1
            u = max(1, int(z * (1 + ph)))
            gx = int(self.x - self.ox + self.face * (28 + ph * 22) * z - 2.5 * u)
            gy = int(self.y - self.oy - (8 + ph * 45) * z)
            for bx, by, bw, bh in ((0, 0, 5, 1), (3, 1, 1, 1), (2, 2, 1, 1), (1, 3, 1, 1), (0, 4, 5, 1)):
                r = (gx + bx * u, gy + by * u, bw * u, bh * u)
                out.append(r)
                self.c.create_rectangle(r[0], r[1], r[0] + r[2], r[1] + r[3],
                                        fill="#5F7FA0", outline="", tags="z")
        return out

    # ---------------------------------------------------------- menú
    def build_menu(self):
        m = tk.Menu(self.root, tearoff=0)
        m.add_command(label="⚙ Configuración", command=self.open_settings)
        m.add_separator()
        m.add_command(label="📝 Traer una nota", command=lambda: self.start_bring("note"))
        m.add_command(label="🖼 Traer un meme", command=lambda: self.start_bring("meme"))
        if IS_WIN:
            m.add_command(label="🖱 Robar el cursor", command=self.start_chase)
        m.add_command(label="🐾 Ir a dejar huellas", command=self.start_mud)
        m.add_command(label="😴 Dormir en la esquina", command=self.go_corner)
        m.add_command(label="🧹 Limpiar huellas", command=self.clear_prints)
        m.add_separator()
        m.add_command(label="❌ Salir", command=self.quit)
        self.menu = m

    def show_menu(self, e):
        if not self.hit(e):
            return
        try:
            self.menu.tk_popup(e.x_root, e.y_root)
        finally:
            self.menu.grab_release()

    def quit(self):
        save_settings(self.cfg)
        for w in self.wins:
            try:
                w.destroy()
            except Exception:
                pass
        self.root.destroy()

    # ---------------------------------------------------------- configuración
    def theme(self, w):
        bg, fg, ac = self.cfg["panel_bg"], self.cfg["panel_fg"], self.cfg["panel_accent"]
        cls = w.winfo_class()
        try:
            if cls in ("Toplevel", "Frame"):
                w.configure(bg=bg)
            elif cls in ("Label", "Checkbutton"):
                w.configure(bg=bg, fg=fg)
                if cls == "Checkbutton":
                    w.configure(selectcolor="white", activebackground=bg)
            elif cls == "Scale":
                w.configure(bg=bg, fg=fg, troughcolor=ac, highlightthickness=0)
            elif cls == "Button":
                w.configure(bg=ac, fg=fg, activebackground=bg, relief="flat")
            elif cls == "Text":
                w.configure(bg="white", fg="#222222", insertbackground="#222222")
        except tk.TclError:
            pass
        for ch in w.winfo_children():
            self.theme(ch)

    def open_settings(self):
        if self.settings_win is not None and self.settings_win.winfo_exists():
            self.settings_win.lift()
            return
        win = tk.Toplevel(self.root)
        win.title("Configuración del zorro")
        win.geometry("400x600+120+80")
        try:
            win.attributes("-topmost", True)
        except tk.TclError:
            pass
        self.settings_win = win
        nb = ttk.Notebook(win)
        nb.pack(fill="both", expand=True)
        t1, t2, t3 = tk.Frame(nb), tk.Frame(nb), tk.Frame(nb)
        nb.add(t1, text="Travesuras")
        nb.add(t2, text="Notas")
        nb.add(t3, text="Aspecto")

        def check(parent, label, key, state="normal"):
            v = tk.BooleanVar(value=self.cfg[key])
            tk.Checkbutton(parent, text=label, variable=v, state=state,
                           command=lambda: self.save(key, v.get())).pack(anchor="w", padx=14)

        def slider(parent, label, key, lo, hi, res, cb=None):
            tk.Label(parent, text=label).pack(anchor="w", padx=14, pady=(8, 0))
            s = tk.Scale(parent, from_=lo, to=hi, resolution=res, orient="horizontal")
            s.set(self.cfg[key])

            def on(v):
                self.save(key, float(v) if res < 1 else int(float(v)))
                if cb:
                    cb()
            s.configure(command=on)
            s.pack(fill="x", padx=14)

        def button(parent, label, cmd):
            tk.Button(parent, text=label, command=cmd).pack(fill="x", padx=14, pady=2)

        def color(parent, label, key):
            def pick():
                col = colorchooser.askcolor(self.cfg[key], title=label, parent=win)[1]
                if col:
                    self.save(key, col)
                    self.theme(win)
            button(parent, label, pick)

        tk.Label(t1, text="Comportamiento", font=("Segoe UI", 12, "bold")).pack(pady=8)
        check(t1, "Pasear libremente por la pantalla", "wander")
        check(t1, "Perseguir y robar el cursor (solo Windows)", "steal",
              "normal" if IS_WIN else "disabled")
        check(t1, "Dejar huellas de barro", "prints", "normal" if self.full else "disabled")
        check(t1, "Traer notas", "notes")
        check(t1, "Traer memes", "memes")
        check(t1, "Sonidos (yip)", "sound")
        slider(t1, "Frecuencia de travesuras", "freq", 1, 5, 1)
        slider(t1, "Velocidad", "speed", 1, 10, 1)
        slider(t1, "Segundos que duran las huellas", "print_secs", 5, 120, 5)
        tk.Label(t1, text="Hacer ahora:").pack(anchor="w", padx=14, pady=(10, 0))
        button(t1, "Traer una nota", lambda: self.start_bring("note"))
        button(t1, "Traer un meme", lambda: self.start_bring("meme"))
        if IS_WIN:
            button(t1, "Robar el cursor", self.start_chase)
        button(t1, "Dormir en la esquina", self.go_corner)
        button(t1, "Limpiar huellas", self.clear_prints)

        tk.Label(t2, text="Mensajes de las notas (uno por línea)",
                 font=("Segoe UI", 11, "bold")).pack(pady=8)
        txt = tk.Text(t2, wrap="word", height=14, font=("Segoe UI", 10))
        txt.pack(fill="both", expand=True, padx=12, pady=4)
        txt.insert("1.0", "\n".join(self.cfg["messages"]))
        txt.bind("<KeyRelease>", lambda e: self.save(
            "messages", [l.strip() for l in txt.get("1.0", "end-1c").splitlines() if l.strip()]))

        def open_memes():
            d = os.path.join(HERE, "memes")
            os.makedirs(d, exist_ok=True)
            try:
                if IS_WIN:
                    os.startfile(d)
                else:
                    os.system(('open "%s"' if IS_MAC else 'xdg-open "%s"') % d)
            except Exception:
                pass
        tk.Label(t2, text="Memes: imágenes .png/.gif/.jpg en la carpeta 'memes'",
                 wraplength=350).pack(pady=(6, 0))
        button(t2, "Abrir carpeta de memes", open_memes)

        tk.Label(t3, text="Aspecto", font=("Segoe UI", 12, "bold")).pack(pady=8)
        slider(t3, "Tamaño del zorro (1 = pequeño, 5 = enorme)", "zoom", 1, 5, 1, self.set_zoom)
        slider(t3, "Minutos de siesta (doble clic)", "sleep_min", 1, 30, 1)
        color(t3, "Color de las huellas", "mud")
        color(t3, "Color de las notas", "note_bg")
        color(t3, "Color de fondo de este panel", "panel_bg")
        color(t3, "Color del texto del panel", "panel_fg")
        color(t3, "Color de acento del panel", "panel_accent")

        def reset():
            for key in ("zoom", "sleep_min", "mud", "note_bg", "panel_bg", "panel_fg", "panel_accent"):
                self.cfg[key] = DEFAULTS[key]
            save_settings(self.cfg)
            self.set_zoom()
            win.destroy()
            self.open_settings()
        button(t3, "Restablecer aspecto", reset)
        self.theme(win)

    def run(self):
        self.root.mainloop()


if __name__ == "__main__":
    Fox().run()
