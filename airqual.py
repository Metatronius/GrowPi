from gpiozero import MCP3008
import time

analog_input = MCP3008(channel=0)

def readQual():
    reading = analog_input.value
    print("Reading={:.2f}".format(reading))

while true:
    readQual()
    time.sleep(1)