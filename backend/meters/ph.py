from gpiozero import MCP3008

class PHMeter:
    def __init__(self, pin, slope=-5.6548, intercept=15.509, cal_type="linear", a=0, b=0, c=0):
        self.sensor = MCP3008(channel=pin)
        self.slope = slope
        self.intercept = intercept
        self.cal_type = cal_type
        self.a = a
        self.b = b
        self.c = c

    def read_voltage(self):
        return self.sensor.value * 3.3

    def read_ph(self):
        voltage = self.read_voltage()
        if self.cal_type == "quadratic":
            return self.a * voltage ** 2 + self.b * voltage + self.c
        else:
            return self.slope * voltage + self.intercept
