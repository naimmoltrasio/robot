import time
import board
import busio
import sys
import tty
import termios
from adafruit_pca9685 import PCA9685
from adafruit_motor import servo
import select

# Configuración de I2C y PCA9685
i2c = busio.I2C(board.SCL, board.SDA)
pca = PCA9685(i2c)
pca.frequency = 50

# Configuración del servo en el canal 0
servo_x = servo.Servo(pca.channels[0])

# Configuración de la terminal para lectura no bloqueante
def getch():
    fd = sys.stdin.fileno()
    old_settings = termios.tcgetattr(fd)
    try:
        tty.setraw(fd)
        rlist, _, _ = select.select([sys.stdin], [], [], 0.1)
        if rlist:
            ch = sys.stdin.read(1)
        else:
            ch = None
    finally:
        termios.tcsetattr(fd, termios.TCSADRAIN, old_settings)
    return ch

# Función para mover el servo en bucle simulando una vuelta completa en ambas direcciones
def move_servo_loop():
    angle = 0
    step = 2  # Incremento de movimiento

    while True:
        # Mover el servo de 0 a 180 grados
        while angle <= 180:
            servo_x.angle = max(0, min(180, angle))
            time.sleep(0.05)  # Pequeña pausa para hacer el movimiento rápido
            angle += step

            # Verificar si se presionó 'q' para salir
            ch = getch()
            if ch == 'q':
                print("Saliendo del bucle...")
                return

        # Volver de 180 a 0 grados
        while angle >= 0:
            servo_x.angle = max(0, min(180, angle))
            time.sleep(0.05)  # Pequeña pausa para hacer el movimiento rápido
            angle -= step

            # Verificar si se presionó 'q' para salir
            ch = getch()
            if ch == 'q':
                print("Saliendo del bucle...")
                return

        # Reset angle to 0 for next iteration
        angle = 0

# Ejecutar la función para mover el servo en bucle
move_servo_loop()

# Apagar el PCA9685
pca.deinit()
