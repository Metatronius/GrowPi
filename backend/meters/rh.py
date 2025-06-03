from gpiozero import *
import time

class RHMeter:
    def __init__(self, pin):
        self.sensor = MCP3008(channel=pin)

    def read_rh(self):
        voltage = self.sensor.value * 3.3
        rh = (voltage - 0.8) / 0.0062
        return round(rh, 2)
