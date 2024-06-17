from picamera2 import Picamera2
import cv2
import time
import os
import board
import busio
from adafruit_pca9685 import PCA9685
from adafruit_motor import servo

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
face_cascade = cv2.CascadeClassifier(cascade_path)

# Inicializar la cámara
picam2 = Picamera2()
config = picam2.create_preview_configuration(main={"format": "RGB888", "size": (640, 480)})
picam2.configure(config)
picam2.start()

# Esperar un momento para que la cámara se inicialice
time.sleep(2)

# Función para mover el servo
def move_servo(face_x, frame_width):
    # Calcular el error en la posición del rostro
    error_x = face_x - frame_width / 2

    # Ajustar ángulo del servo en el eje X
    if abs(error_x) > 15:
        servo_x.angle = max(0, min(180, servo_x.angle - error_x / 50))

# Bucle principal
while True:
    # Capturar frame por frame
    frame = picam2.capture_array()

    # Convertir a escala de grises
    gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)

    # Detectar rostros
    faces = face_cascade.detectMultiScale(gray, scaleFactor=1.1, minNeighbors=5, minSize=(30, 30))

    # Dibujar rectángulos alrededor de los rostros y mover el servo
    for (x, y, w, h) in faces:
        cv2.rectangle(frame, (x, y), (x+w, y+h), (255, 0, 0), 2)
        face_center_x = x + w / 2
        move_servo(face_center_x, frame.shape[1])

    # Mostrar el frame
    cv2.imshow('frame', frame)

    # Salir del bucle al presionar 'q'
    if cv2.waitKey(1) & 0xFF == ord('q'):
        break

# Liberar la cámara y cerrar ventanas
picam2.stop()
cv2.destroyAllWindows()

# Apagar el PCA9685
pca.deinit()
