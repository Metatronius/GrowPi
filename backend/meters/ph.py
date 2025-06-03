from gpiozero import *
import time

class PHMeter:
    def __init__(self, pin):
        self.sensor = MCP3008(channel=pin)

    def read_ph(self):
        voltage = self.sensor.value * 3.3
        ph = (-5.6548 * voltage) + 15.509 #as per Atlas Scientific's specifications
        return round(ph, 2)
