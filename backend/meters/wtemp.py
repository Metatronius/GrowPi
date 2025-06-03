from w1thermsensor import W1ThermSensor
import time

class WaterTemperatureSensor:
    sensor = None
    def __init__(self, sensor):
        self.sensor =W1ThermSensor(W1ThermSensor.THERM_SENSOR_DS18B20, "00000588806a")
        

    def read_temp(self):
        temperature = self.sensor.get_temperature(W1ThermSensor.DEGREES_F)
        return temperature
        