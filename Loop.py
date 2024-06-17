import threading
from multiprocessing import Process, Queue
import time
import cv2
from flask import Flask, request, jsonify
import asl_transcription as al
import pyttsx3
import speech_recognition as sr
import matplotlib.pyplot as plt
import matplotlib.image as mpimg

app = Flask(__name__)

# Configuraciones iniciales
_Servo1UL = 250
_Servo0UL = 230
_Servo1LL = 75
_Servo0LL = 70

ServoBlaster = open('/dev/servoblaster', 'w')

webcam = cv2.VideoCapture(0)
webcam.set(cv2.CAP_PROP_FRAME_WIDTH, 320)
webcam.set(cv2.CAP_PROP_FRAME_HEIGHT, 240)

frontalface = cv2.CascadeClassifier("haarcascade_frontalface_alt2.xml")
profileface = cv2.CascadeClassifier("haarcascade_profileface.xml")

face = [0, 0, 0, 0]
Cface = [0, 0]
lastface = 0

Servo0CP = Queue()
Servo1CP = Queue()
Servo0DP = Queue()
Servo1DP = Queue()
Servo0S = Queue()
Servo1S = Queue()

def CamRight( distance, speed ):		# To move right, we are provided a distance to move and a speed to move.
	global _Servo0CP			# We Global it so  everyone is on the same page about where the servo is...
	if not Servo0CP.empty():		# Read it's current position given by the subprocess(if it's avalible)-
		_Servo0CP = Servo0CP.get()	# 	and set the main process global variable.
	_Servo0DP = _Servo0CP + distance	# The desired position is the current position + the distance to move.
	if _Servo0DP > _Servo0UL:		# But if you are told to move further than the servo is built go...
		_Servo0DP = _Servo0UL		# Only move AS far as the servo is built to go.
	Servo0DP.put(_Servo0DP)			# Send the new desired position to the subprocess
	Servo0S.put(speed)			# Send the new speed to the subprocess
	return;

def CamLeft(distance, speed):			# Same logic as above
	global _Servo0CP
	if not Servo0CP.empty():
		_Servo0CP = Servo0CP.get()
	_Servo0DP = _Servo0CP - distance
	if _Servo0DP < _Servo0LL:
		_Servo0DP = _Servo0LL
	Servo0DP.put(_Servo0DP)
	Servo0S.put(speed)
	return;


def CamDown(distance, speed):			# Same logic as above
	global _Servo1CP
	if not Servo1CP.empty():
		_Servo1CP = Servo1CP.get()
	_Servo1DP = _Servo1CP + distance
	if _Servo1DP > _Servo1UL:
		_Servo1DP = _Servo1UL
	Servo1DP.put(_Servo1DP)
	Servo1S.put(speed)
	return;


def CamUp(distance, speed):			# Same logic as above
	global _Servo1CP
	if not Servo1CP.empty():
		_Servo1CP = Servo1CP.get()
	_Servo1DP = _Servo1CP - distance
	if _Servo1DP < _Servo1LL:
		_Servo1DP = _Servo1LL
	Servo1DP.put(_Servo1DP)
	Servo1S.put(speed)
	return;

def P0():
    speed = .1
    _Servo0CP = 99
    _Servo0DP = 100
    while True:
        time.sleep(speed)
        if Servo0CP.empty():
            Servo0CP.put(_Servo0CP)
        if not Servo0DP.empty():
            _Servo0DP = Servo0DP.get()
        if not Servo0S.empty():
            _Servo0S = Servo0S.get()
            speed = .1 / _Servo0S
        if _Servo0CP < _Servo0DP:
            _Servo0CP += 1
            Servo0CP.put(_Servo0CP)
            ServoBlaster.write('0=' + str(_Servo0CP) + '\n')
            ServoBlaster.flush()
            Servo0CP.get()
        elif _Servo0CP > _Servo0DP:
            _Servo0CP -= 1
            Servo0CP.put(_Servo0CP)
            ServoBlaster.write('0=' + str(_Servo0CP) + '\n')
            ServoBlaster.flush()
            Servo0CP.get()
        elif _Servo0CP == _Servo0DP:
            _Servo0S = 1

def P1():
    speed = .1
    _Servo1CP = 99
    _Servo1DP = 100
    while True:
        time.sleep(speed)
        if Servo1CP.empty():
            Servo1CP.put(_Servo1CP)
        if not Servo1DP.empty():
            _Servo1DP = Servo1DP.get()
        if not Servo1S.empty():
            _Servo1S = Servo1S.get()
            speed = .1 / _Servo1S
        if _Servo1CP < _Servo1DP:
            _Servo1CP += 1
            Servo1CP.put(_Servo1CP)
            ServoBlaster.write('1=' + str(_Servo1CP) + '\n')
            ServoBlaster.flush()
            Servo1CP.get()
        elif _Servo1CP > _Servo1DP:
            _Servo1CP -= 1
            Servo1CP.put(_Servo1CP)
            ServoBlaster.write('1=' + str(_Servo1CP) + '\n')
            ServoBlaster.flush()
            Servo1CP.get()
        elif _Servo1CP == _Servo1DP:
            _Servo1S = 1

Process(target=P0, args=()).start()
Process(target=P1, args=()).start()
time.sleep(1)

def tracking_loop():
    while not stop_thread.is_set():
        faceFound = False
        # El código del seguimiento aquí

def stop_all():
    stop_thread.set()
    webcam.release()
    ServoBlaster.close()

stop_thread = threading.Event()
tracking_thread = threading.Thread(target=tracking_loop)
tracking_thread.start()

conv = {"activo": False, "opcion": None}

def tts(frase):
    engine = pyttsx3.init()

    rate = engine.getProperty('rate')
    engine.setProperty('rate', rate - 50)

    volume = engine.getProperty('volume')
    engine.setProperty('volume', volume + 0.25)

    engine.say(frase)

    engine.runAndWait()

def stt():
    recognizer = sr.Recognizer()

    with sr.Microphone() as source:
        print("Por favor, hable ahora...")
        
        recognizer.adjust_for_ambient_noise(source)
        print("Escuchando...")
        
        audio = recognizer.listen(source)

    try:
        texto = recognizer.recognize_google(audio, language="es-ES")
        return texto
    except sr.UnknownValueError:
        return None
    except sr.RequestError as e:
        return None
    
def pillaOpcio():
     data = request.get_json()
     conv['activo'] = True
     conv['opcion'] = data.get('opcion')

asl = {
    "a": "../Robot/asl/a.png",
    "b": "../Robot/asl/b.png",
    "c": "../Robot/asl/c.png",
    "d": "../Robot/asl/d.png",
    "e": "../Robot/asl/e.png",
    "f": "../Robot/asl/f.png",
    "g": "../Robot/asl/g.png",
    "h": "../Robot/asl/h.png",
    "i": "../Robot/asl/i.png",
    "j": "../Robot/asl/j.png",
    "k": "../Robot/asl/k.png",
    "l": "../Robot/asl/l.png",
    "m": "../Robot/asl/m.png",
    "n": "../Robot/asl/n.png",
    "o": "../Robot/asl/o.png",
    "p": "../Robot/asl/p.png",
    "q": "../Robot/asl/q.png",
    "r": "../Robot/asl/r.png",
    "s": "../Robot/asl/s.png",
    "t": "../Robot/asl/t.png",
    "u": "../Robot/asl/u.png",
    "v": "../Robot/asl/v.png",
    "w": "../Robot/asl/w.png",
    "x": "../Robot/asl/x.png",
    "y": "../Robot/asl/y.png",
    "z": "../Robot/asl/z.png"
}

espacio = "nada.jpg"

def transcripcion(texto):
    global asl, espacio
    texto = texto.lower()
    texto_transcrito = []
    
    for letra in texto:
        if letra in asl:
            texto_transcrito.append(asl[letra])
        else:
            texto_transcrito.append(espacio)
    return texto_transcrito

def mostrar_transcripcion(texto_transcrito):
    fig, ax = plt.subplots(1, len(texto_transcrito), figsize=(5, 5))
    for i, imagen_path in enumerate(texto_transcrito):
        img = mpimg.imread(imagen_path)
        ax[i].imshow(img)
        ax[i].axis('off')
    plt.show()

def PartSord():
    frase = al.procesar_video() # Comença hand tracking, passem de signe a lletra (Image to text)

    tts(frase) # De lletra a parlada (Text to speech)

    PartParl()
# Quan hi ha 3 espais seguits al text ("15 segons sense mans") passem a part parl (PartParl())

def PartParl():
    frase = stt() # Comença escoltant (Speech to text)

                   # Transcriu a ASL (Text to image)
    transcripcion(frase)
    mostrar_transcripcion() # Mostra per pantalla els signes

    PartSord() # TPassem a part sord (PartSord())

def Conversa():
    while not stop_thread.is_set():
        if conv["activo"]:
            if conv['opcion'] == 'D': #Empieza el deaf (primero hand tracking)
                PartSord()
                PartParl()
            else: #Empieza el que habla
                 PartParl()
                 PartSord()
                 
        time.sleep(1)

def flask_thread():
    app.run(host='0.0.0.0', port=5000, debug=False, use_reloader=False)

def tracking_loop():
    global lastface
    while not stop_thread.is_set():
        faceFound = False
        
        # Capturar imagen de la cámara
        ret, aframe = webcam.read()
        if not ret:
            continue  # Si no se pudo capturar una imagen, continúa con la próxima iteración
        
        # Buscar rostros
        if lastface == 0 or lastface == 1:
            gray = cv2.cvtColor(aframe, cv2.COLOR_BGR2GRAY)
            fface = frontalface.detectMultiScale(gray, 1.3, 4, cv2.CASCADE_SCALE_IMAGE, (60, 60))
            if fface != ():
                lastface = 1
                faceFound = True
                face = fface[0]  # Tomar el primer rostro detectado

        if not faceFound and (lastface == 0 or lastface == 2):
            gray = cv2.cvtColor(aframe, cv2.COLOR_BGR2GRAY)
            pfacer = profileface.detectMultiScale(gray, 1.3, 4, cv2.CASCADE_SCALE_IMAGE, (80, 80))
            if pfacer != ():
                lastface = 2
                faceFound = True
                face = pfacer[0]

        if not faceFound and (lastface == 0 or lastface == 3):
            gray = cv2.cvtColor(cv2.flip(aframe, 1), cv2.COLOR_BGR2GRAY)
            pfacel = profileface.detectMultiScale(gray, 1.3, 4, cv2.CASCADE_SCALE_IMAGE, (80, 80))
            if pfacel != ():
                lastface = 3
                faceFound = True
                face = pfacel[0]

        # Si se encontró un rostro, actualizar la posición de los servomotores
        if faceFound:
            x, y, w, h = face
            Cface[0] = w / 2 + x
            Cface[1] = h / 2 + y
            adjust_servo(Cface)
        else:
            face = [0, 0, 0, 0]
            lastface = 0

        print(f"Centro del rostro: {Cface[0]}, {Cface[1]}")

def adjust_servo(Cface):
    # Logica para mover los servos basado en la posición del rostro
    if Cface[0] > 180:
        CamLeft(5, 1)
    elif Cface[0] < 140:
        CamRight(5, 1)
    if Cface[1] > 140:
        CamDown(5, 1)
    elif Cface[1] < 100:
        CamUp(5, 1)

def stop_all():
    stop_thread.set()
    webcam.release()
    ServoBlaster.close()

def Conversa():
    data = request.get_json()

if __name__ == '__main__':
    # Inicializar y comenzar los hilos de Flask y seguimiento
    flask_app_thread = threading.Thread(target=flask_thread)
    flask_app_thread.start()
    
    # Inicia los procesos de los servomotores
    Process(target=P0, args=()).start()
    Process(target=P1, args=()).start()
    
    tracking_thread = threading.Thread(target=tracking_loop)
    tracking_thread.start()

    try:
        Conversa()
    except KeyboardInterrupt:
        print("Deteniendo todos los procesos...")
        stop_all()
        tracking_thread.join()
        print("Procesos detenidos correctamente.")
