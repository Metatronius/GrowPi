import board
from adafruit_htu21d import HTU21D
import time
class RHMeter:
    def __init__(self):
        # Create sensor object, communicating over the board's default I2C bus
        i2c = board.I2C()  # uses board.SCL and board.SDA
        # i2c = board.STEMMA_I2C()  # For using the built-in STEMMA QT connector on a microcontroller
        self.sensor = HTU21D(i2c)

    def read_rh(self):
        rh_value = self.sensor.relative_humidity
        return rh_value
