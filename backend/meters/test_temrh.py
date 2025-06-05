import board
from adafruit_htu21d import HTU21D

i2c = board.I2C()
sensor = HTU21D(i2c)
print("Temperature:", sensor.temperature)
print("Humidity:", sensor.relative_humidity)