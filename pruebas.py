import asl_transcription as al
import speech_recognition as sr
import pyttsx3
import time
import warnings
import tkinter as tk
from PIL import Image, ImageTk
from tkinter import Canvas
from unidecode import unidecode
import threading
import requests

warnings.filterwarnings('ignore')

asl = {
    "a": "asl/a.png",
    "b": "asl/b.png",
    "c": "asl/c.png",
    "d": "asl/d.png",
    "e": "asl/e.png",
    "f": "asl/f.png",
    "g": "asl/g.png",
    "h": "asl/h.png",
    "i": "asl/i.png",
    "j": "asl/j.png",
    "k": "asl/k.png",
    "l": "asl/l.png",
    "m": "asl/m.png",
    "n": "asl/n.png",
    "o": "asl/o.png",
    "p": "asl/p.png",
    "q": "asl/q.png",
    "r": "asl/r.png",
    "s": "asl/s.png",
    "t": "asl/t.png",
    "u": "asl/u.png",
    "v": "asl/v.png",
    "w": "asl/w.png",
    "x": "asl/x.png",
    "y": "asl/y.png",
    "z": "asl/z.png"
}

espacio = "nada.jpg"

# Funciones relacionadas con la UI
def mostrar_mensaje(mensaje, duracion=None):
    root = tk.Tk()
    root.attributes("-fullscreen", True)
    root.lift()
    root.attributes('-topmost', True)
    label = tk.Label(root, text=mensaje, font=("Helvetica", 48), fg="white", bg="black")
    label.pack(expand=True)
    root.update()
    root.after(0, lambda: root.attributes('-topmost', False))
    if duracion:
        root.after(duracion * 1000, root.destroy)
    root.mainloop()
    return root

def mostrar_imagen(imagen_path, duracion=2):
    root = tk.Tk()
    root.attributes("-fullscreen", True)
    root.lift()
    root.attributes('-topmost', True)

    img = Image.open(imagen_path)
    img.thumbnail((root.winfo_screenwidth(), root.winfo_screenheight()), Image.LANCZOS)
    img = ImageTk.PhotoImage(img)

    label = tk.Label(root, image=img)
    label.image = img
    label.pack(expand=True)
    root.update()
    root.after(0, lambda: root.attributes('-topmost', False))
    root.after(duracion * 1000, root.destroy)
    root.mainloop()

# Funciones relacionadas con TTS
def tts(frase):
    mostrar_imagen('boca.jpg', duracion=3)
    engine = pyttsx3.init()
    rate = engine.getProperty('rate')
    engine.setProperty('rate', rate - 50)
    volume = engine.getProperty('volume')
    engine.setProperty('volume', volume + 0.25)
    engine.say(frase)
    engine.runAndWait()

# Funciones relacionadas con STT
def stt():
    recognizer = sr.Recognizer()

    root = tk.Tk()
    root.attributes("-fullscreen", True)
    root.lift()
    root.attributes('-topmost', True)
    label = tk.Label(root, text="Escuchando...", font=("Helvetica", 48), fg="white", bg="black")
    label.pack(expand=True)
    root.update()
    root.after(0, lambda: root.attributes('-topmost', False))

    with sr.Microphone() as source:
        recognizer.adjust_for_ambient_noise(source)
        audio = recognizer.listen(source)

    try:
        texto = recognizer.recognize_google(audio, language="es-ES")
    except sr.UnknownValueError:
        texto = None
    except sr.RequestError as e:
        texto = None

    root.destroy()
    return texto

# Funciones relacionadas con ASL
def transcripcion(texto):
    global asl, espacio
    texto = unidecode(texto.lower())
    texto_transcrito = []
    for letra in texto:
        if letra in asl:
            texto_transcrito.append(asl[letra])
        else:
            texto_transcrito.append(espacio)
    return texto_transcrito

def mostrar_transcripcion(texto_transcrito):
    root = tk.Tk()
    root.attributes("-fullscreen", True)

    screen_width = root.winfo_screenwidth()
    screen_height = root.winfo_screenheight()

    max_image_width = screen_width // len(texto_transcrito)
    max_image_height = screen_height // 2

    canvas = Canvas(root, bg='white')
    canvas.pack(expand=True, fill='both')

    images = []
    x_offset = 20
    for imagen_path in texto_transcrito:
        img = Image.open(imagen_path)
        img.thumbnail((max_image_width, max_image_height), Image.LANCZOS)
        img = ImageTk.PhotoImage(img)

        images.append(img)
        canvas.create_image(x_offset, screen_height // 4, anchor='nw', image=img)
        x_offset += img.width() + 20

    root.lift()
    root.attributes('-topmost', True)
    root.after(0, lambda: root.attributes('-topmost', False))
    root.update()
    root.after(5000, root.destroy)
    root.mainloop()

# Funciones para iniciar los diferentes modos
def PartSord():
    frase = al.inicia()  # Comienza el reconocimiento de signos
    tts(frase)  # Convierte texto a voz
    time.sleep(5)
    pantalla_carga()  # Volver a la pantalla de carga después del intercambio

def PartParl():
    frase = stt()  # Comienza el reconocimiento de voz
    if frase:
        t = transcripcion(frase)  # Convierte texto a signos
        mostrar_transcripcion(t)  # Muestra los signos en la pantalla
    pantalla_carga()  # Volver a la pantalla de carga después del intercambio

def leer_senal():
    try:
        response = requests.get('http://192.168.1.30:5000/get_signal')
        if response.status_code == 200:
            return response.text
        else:
            return None
    except requests.exceptions.RequestException:
        return None

def pantalla_carga():
    root = tk.Tk()
    root.title("Pantalla de Carga")
    root.attributes("-fullscreen", True)

    label = tk.Label(root, text="Esperando opción...", font=("Helvetica", 48), fg="white", bg="black")
    label.pack(expand=True)

    '''def on_key(event):
        key = event.char.lower()
        if key == "p":
            root.destroy()
            PartParl()
        elif key == "s":
            root.destroy()
            PartSord()
        elif key == "e":
            root.destroy()
            black_screen()'''
    def verificar_senal():
        senal = leer_senal()
        if senal:
            print(f"Señal recibida {senal}")
            if senal == 'p':
                root.destroy()
                PartParl()
            elif senal == 's':
                root.destroy()
                PartSord()
            elif senal == 'e':
                root.destroy()
                black_screen()
        else:
            root.after(1000, verificar_senal)

    root.after(1000, verificar_senal)
    root.mainloop()

def black_screen():
    root = tk.Tk()
    root.attributes("-fullscreen", True)
    root.configure(bg='black')
    root.mainloop()

if __name__ == '__main__':
    pantalla_carga()
