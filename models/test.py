import RPi.GPIO as GPIO
from adafruit_bno055 import BNO055_I2C
import board
import busio


i2c = busio.I2C(board.SCL, board.SDA)
sensor = BNO055_I2C(i2c)

print(sensor.temperature)
print(sensor.euler)
print(sensor.gravity)