from w1thermsensor import W1ThermSensor

class WaterTemperatureSensor:
    def __init__(self):
        self.sensor = W1ThermSensor()  # Uses the first detected sensor

    def read_temp(self):
        # Returns temperature in Fahrenheit
        celsius = self.sensor.get_temperature()
        fahrenheit = celsius * 9 / 5 + 32
        return round(fahrenheit, 2)
