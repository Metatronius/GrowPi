from gpiozero import *
import time

class AirQuality:
    def __init__(self,pin):
        self.dig_in=GPIODevice(pin)

    def read_aq(self):
        reading = self.dig_in.value
        return reading


