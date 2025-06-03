from gpiozero import *
import time

class PHMeter:
    def __init__(self, pin):
        self.sensor = MCP3008(channel=pin)

    def read_ph(self):
        voltage = self.sensor.value * 3.3
        ph = 7 + ((2.5 - voltage) / 0.18)
        return round(ph, 2)
