import numpy as np
import pickle
import time
import tkinter as tk
from tkinter import Label, Text
from PIL import Image, ImageTk
from sklearn.ensemble import RandomForestClassifier
import mediapipe as mp
from picamera2 import Picamera2, Preview
import cv2 as cv
import os
import board
import busio
from adafruit_pca9685 import PCA9685
from adafruit_motor import servo

# Inicializar variables globales fuera de la función
camera_open = False
img_refs = []  # Mantener una referencia de las imágenes
last_seen_time = time.time()
last_space_time = time.time()
last_predicted_character = ''
last_character_time = time.time()
character_written = False
texto_generado = ""

# Configuración de I2C y PCA9685
i2c = busio.I2C(board.SCL, board.SDA)
pca = PCA9685(i2c)
pca.frequency = 50

# Configuración del servo
servo_x = servo.Servo(pca.channels[0])

# Inicializar posición del servo
servo_x.angle = 90
time.sleep(1)

# Ruta del clasificador preentrenado de rostros
cascade_path = os.path.join(os.path.dirname(__file__), 'haarcascade_frontalface_default.xml')
face_cascade = cv.CascadeClassifier(cascade_path)

# Función para mover el servo
def move_servo(face_x, frame_width):
    # Calcular el error en la posición del rostro
    error_x = face_x - frame_width / 2

    # Ajustar ángulo del servo en el eje X
    if abs(error_x) > 15:
        servo_x.angle = max(0, min(180, servo_x.angle - error_x / 50))

def inicia():
    global img_refs, texto_transcrito, label_video, root, root_cargando, picam2

    def augment_landmarks(landmarks, num_variations=100):
        augmented_data = []
        for _ in range(num_variations):
            new_landmarks = np.copy(landmarks)
            noise = np.random.normal(loc=0.0, scale=0.01, size=new_landmarks.shape)
            new_landmarks += noise
            scale = np.random.uniform(0.95, 1.05)
            new_landmarks *= scale
            translation = np.random.uniform(-0.01, 0.01, size=new_landmarks.shape[1])
            new_landmarks += translation
            augmented_data.append(new_landmarks)
        return np.array(augmented_data)

    model = pickle.load(open('./model.pkl', 'rb'))

    # Inicialización de MediaPipe
    mp_hands = mp.solutions.hands
    mp_drawing = mp.solutions.drawing_utils
    mp_drawing_styles = mp.solutions.drawing_styles
    hands = mp_hands.Hands(static_image_mode=True, max_num_hands=1, min_detection_confidence=0.5)

    # Labels
    labels_dict = {0: 'A', 1: 'B', 2: 'C', 3: 'D', 4: 'E', 5: 'F', 6: 'G', 7: 'H', 8: 'I', 9: 'J', 10: 'K', 11: 'L', 12: 'M', 13: 'N', 14: 'O', 
                   15: 'P', 16: 'Q', 17: 'R', 18: 'S', 19: 'T', 20: 'U', 21: 'V', 22: 'W', 23: 'X', 24: 'Y'}

    def abrir_camara():
        global camera_open, last_seen_time, last_space_time, picam2
        if not camera_open:
            picam2.start()
            camera_open = True
            last_seen_time = time.time()
            last_space_time = time.time()
            root.after(10, procesar_video)

    def cerrar_camara():
        global camera_open, picam2
        if camera_open:
            picam2.stop()
            camera_open = False

    def procesar_video():
        global camera_open, last_seen_time, last_space_time, last_predicted_character, last_character_time, character_written, texto_generado, img_refs
        if camera_open:
            data_aux = []
            x_ = []
            y_ = []

            frame = picam2.capture_array()
            gray = cv.cvtColor(frame, cv.COLOR_BGR2GRAY)
            faces = face_cascade.detectMultiScale(gray, scaleFactor=1.1, minNeighbors=5, minSize=(30, 30))

            # Detectar y mover el servo para seguir el rostro
            for (x, y, w, h) in faces:
                face_center_x = x + w / 2
                move_servo(face_center_x, frame.shape[1])

            H, W, _ = frame.shape
            results = hands.process(frame)

            if results.multi_hand_landmarks:
                last_seen_time = time.time()  # Reset the last seen time when hands are detected
                for hand_landmarks in results.multi_hand_landmarks:
                    mp_drawing.draw_landmarks(
                        frame,
                        hand_landmarks,
                        mp_hands.HAND_CONNECTIONS,
                        mp_drawing_styles.get_default_hand_landmarks_style(),
                        mp_drawing_styles.get_default_hand_connections_style())

                for hand_landmarks in results.multi_hand_landmarks:
                    for i in range(len(hand_landmarks.landmark)):
                        x = hand_landmarks.landmark[i].x
                        y = hand_landmarks.landmark[i].y
                        x_.append(x)
                        y_.append(y)

                    for i in range(len(hand_landmarks.landmark)):
                        x = hand_landmarks.landmark[i].x
                        y = hand_landmarks.landmark[i].y
                        data_aux.append(x - min(x_))
                        data_aux.append(y - min(y_))

                x1 = int(min(x_) * W)
                y1 = int(min(y_) * H)
                x2 = int(max(x_) * W)
                y2 = int(max(y_) * H)

                # Predicción usando el modelo
                prediction = model.predict([np.asarray(data_aux)])
                predicted_character = labels_dict[int(prediction[0])]

                # Dibujar un rectángulo y mostrar la predicción en el marco
                cv.rectangle(frame, (x1, y1), (x2, y2), (0, 0, 0), 2)
                cv.putText(frame, predicted_character, (x1, y1 - 10), cv.FONT_HERSHEY_SIMPLEX, 1, (0, 0, 0), 2, cv.LINE_AA)

                # Verificar si la misma letra se mantiene durante 3 segundos
                if predicted_character == last_predicted_character:
                    if time.time() - last_character_time > 3 and not character_written:
                        texto_generado += predicted_character
                        texto_transcrito.insert(tk.END, predicted_character)  # Actualizar el texto en Tkinter
                        character_written = True
                else:
                    last_predicted_character = predicted_character
                    last_character_time = time.time()
                    character_written = False

            # Si no se detecta ninguna mano en 5 segundos, añadir un espacio
            if time.time() - last_seen_time > 5 and time.time() - last_seen_time <= 10:
                texto_generado += " "
                texto_transcrito.insert(tk.END, " ")  # Actualizar el texto en Tkinter
                last_space_time = time.time()  # Reset el tiempo de espacio para no añadir múltiples espacios

            # Si no se detecta ninguna mano en 15 segundos, cerrar la cámara y salir de la aplicación
            if time.time() - last_seen_time > 15:
                cerrar_camara()
                root.destroy()  # Destruir completamente la ventana de Tkinter
                return

            # Convertir el cuadro de OpenCV en un formato compatible con Tkinter
            img = Image.fromarray(frame)
            imgtk = ImageTk.PhotoImage(image=img)

            # Añadir la referencia de la imagen a la lista para mantener las referencias
            img_refs.append(imgtk)
            label_video.imgtk = imgtk
            label_video.configure(image=imgtk)

            # Volver a procesar el video después de 10 ms
            if camera_open:
                root.after(10, procesar_video)

    # Inicializar la ventana de "Cargando..."
    def mostrar_cargando():
        global root_cargando
        root_cargando = tk.Toplevel()
        root_cargando.attributes("-fullscreen", True)
        root_cargando.attributes("-topmost", True)  # Mantener en primer plano
        label_cargando = tk.Label(root_cargando, text="Cargando...", font=("Helvetica", 48), fg="white", bg="black")
        label_cargando.pack(expand=True)
        root_cargando.update()

    def ocultar_cargando():
        global root_cargando
        root_cargando.destroy()
        root.attributes("-topmost", True)  # Poner la ventana principal en primer plano
        root.after(500, lambda: root.attributes("-topmost", False))  # Permitir otras ventanas en primer plano después de 500 ms

    def iniciar_y_abrir_camara():
        mostrar_cargando()
        root.after(2000, start_camera)

    def start_camera():
        abrir_camara()
        ocultar_cargando()

    # Configuración de la interfaz gráfica
    root = tk.Tk()
    root.title("")  # Sin título
    root.attributes("-fullscreen", True)  # Configurar ventana a pantalla completa

    # Mensaje de instrucciones
    mensaje_instrucciones = Label(root, text="Espera 5 segundos para un espacio, o espera 10 segundos para pasar el turno", font=("Helvetica", 16))
    mensaje_instrucciones.pack()

    label_video = Label(root)
    label_video.pack(fill=tk.BOTH, expand=True)  # Llenar toda la pantalla con el video

    # Texto transcrito en la parte inferior
    texto_transcrito = Text(root, height=2, font=("Helvetica", 16))
    texto_transcrito.pack(side=tk.BOTTOM, fill=tk.X)

    # Inicializar Picamera2
    picam2 = Picamera2()
    picam2.configure(picam2.create_still_configuration(main={"size": (640, 480)}))
    picam2.start_preview(Preview.DRM)

    # Iniciar la ventana de "Cargando..." y abrir la cámara después de que la cámara esté lista
    root.after(0, iniciar_y_abrir_camara)

    root.mainloop()
    
    return texto_generado  # Devolver el texto generado cuando se cierra la aplicación

if __name__ == "__main__":
    texto = inicia()
    print("Texto generado:", texto)
