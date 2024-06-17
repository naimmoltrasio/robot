from picamera2 import Picamera2
import cv2
import time

# Inicializar la cámara
picam2 = Picamera2()
config = picam2.create_preview_configuration(main={"format": "RGB888", "size": (640, 480)})
picam2.configure(config)
picam2.start()

# Esperar un momento para que la cámara se inicialice
time.sleep(2)

# Bucle principal
while True:
    # Capturar frame por frame
    frame = picam2.capture_array()

    # Mostrar el frame en una ventana llamada 'frame'
    cv2.imshow('frame', frame)

    # Salir del bucle al presionar 'q'
    if cv2.waitKey(1) & 0xFF == ord('q'):
        break

# Liberar la cámara y cerrar ventanas
picam2.stop()
cv2.destroyAllWindows()
