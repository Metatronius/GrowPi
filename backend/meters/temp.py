from gpiozero import *
import time

class TemperatureSensor:
    def __init__(self, pin):
        self.sensor = MCP3008(channel=pin)

    def read_temp(self):
        voltage = self.sensor.value * 3.3
        temp = (voltage - 0.5) * 100
        return round(temp, 2)
