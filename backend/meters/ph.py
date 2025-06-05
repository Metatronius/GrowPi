from gpiozero import MCP3008

class PHMeter:
    def __init__(self, pin, slope=-5.6548, intercept=15.509):
        self.sensor = MCP3008(channel=pin)
        self.slope = slope
        self.intercept = intercept

    def read_ph(self):
        voltage = self.sensor.value * 3.3
        ph = (self.slope * voltage) + self.intercept
        return round(ph, 2)
